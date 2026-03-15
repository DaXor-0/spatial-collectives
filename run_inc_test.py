import argparse
import csv
import json
import os

import numpy as np

from util import oned_to_hwl_colmajor

from cerebras.sdk.runtime.sdkruntimepybind import SdkRuntime, MemcpyDataType, MemcpyOrder  # pylint: disable=no-name-in-module


DEFAULT_MAX_NX = 4096


def make_u48(words):
  return words[0] + (words[1] << 16) + (words[2] << 32)


def algorithm_name(algo):
  return {
      0: "chain",
      1: "two_phase",
      2: "tree",
      3: "star",
      4: "bine",
  }.get(algo, f"unknown_{algo}")


def collect_timestamps(runner, symbol_time_buf_u16, symbol_time_ref, width, height):
  time_memcpy_hwl_1d = np.zeros(height * width * 6, np.uint32)
  runner.memcpy_d2h(
      time_memcpy_hwl_1d,
      symbol_time_buf_u16,
      0,
      0,
      width,
      height,
      6,
      streaming=False,
      data_type=MemcpyDataType.MEMCPY_16BIT,
      order=MemcpyOrder.COL_MAJOR,
      nonblock=False,
  )
  time_memcpy_hwl = oned_to_hwl_colmajor(height, width, 6, time_memcpy_hwl_1d, np.uint16)

  time_ref_1d = np.zeros(height * width * 3, np.uint32)
  runner.memcpy_d2h(
      time_ref_1d,
      symbol_time_ref,
      0,
      0,
      width,
      height,
      3,
      streaming=False,
      data_type=MemcpyDataType.MEMCPY_16BIT,
      order=MemcpyOrder.COL_MAJOR,
      nonblock=False,
  )
  time_ref_hwl = oned_to_hwl_colmajor(height, width, 3, time_ref_1d, np.uint16)

  time_start = np.zeros((height, width), dtype=int)
  time_end = np.zeros((height, width), dtype=int)
  time_ref = np.zeros((height, width), dtype=int)

  words = np.zeros(3, dtype=np.uint16)
  for w in range(width):
    for h in range(height):
      words[0] = time_memcpy_hwl[(h, w, 0)]
      words[1] = time_memcpy_hwl[(h, w, 1)]
      words[2] = time_memcpy_hwl[(h, w, 2)]
      time_start[(h, w)] = make_u48(words)

      words[0] = time_memcpy_hwl[(h, w, 3)]
      words[1] = time_memcpy_hwl[(h, w, 4)]
      words[2] = time_memcpy_hwl[(h, w, 5)]
      time_end[(h, w)] = make_u48(words)

      words[0] = time_ref_hwl[(h, w, 0)]
      words[1] = time_ref_hwl[(h, w, 1)]
      words[2] = time_ref_hwl[(h, w, 2)]
      time_ref[(h, w)] = make_u48(words) - (w + h + 2)

  return time_start - time_ref, time_end - time_ref


def write_result(dim, algo, is_allred, nx, pw, ph, time_start, time_end, results_file, csv_file):
  elapsed = np.max(time_end) - np.min(time_start)
  total_time = np.max(time_end)
  start_diff = np.max(time_start) - np.min(time_start)

  collective_name = "Allreduce" if is_allred else "Reduce"
  with open(results_file, "a", encoding="utf-8") as result_file:
    result_file.write(
        f"{dim}D, {collective_name} pattern = {algo}, is allreduce = {is_allred}, "
        f"B = {nx}, Pw = {pw}, Ph = {ph}, time = {elapsed}, total_time = {total_time}\n"
    )
    result_file.write(
        f"minimum start = {np.min(time_start)}, maximum start = {np.max(time_start)}, "
        f"diff = {start_diff}\n"
    )

  header = ["Dim", "Pattern", "Algorithm", "Allred", "B", "Pw", "Ph", "time", "total_time", "start_diff"]
  row = [dim, algo, algorithm_name(algo), bool(is_allred), nx, pw, ph, elapsed, total_time, start_diff]
  with open(csv_file, "a", newline="", encoding="utf-8") as out_csv:
    writer = csv.writer(out_csv)
    if out_csv.tell() == 0:
      writer.writerow(header)
    writer.writerow(row)


parser = argparse.ArgumentParser()
parser.add_argument("--name", help="the test name")
parser.add_argument("--cmaddr", help="IP:port for CS system")
parser.add_argument("--results-file", default="results_2d.txt")
parser.add_argument("--csv-file", default="data_2d.csv")
parser.add_argument("--nx-max", type=int, default=None)
args = parser.parse_args()

with open(f"{args.name}/out.json", encoding="utf-8") as json_file:
  compile_data = json.load(json_file)

params = compile_data["params"]
nx = int(params["Nx_start"])
pw = int(params["Pw"])
ph = int(params.get("Ph", 1))
algo = int(params["Algo"])
is_allred = int(params["is_allred"])
measurement_repeats = int(
    params.get("repeats", 1 if os.environ.get("CEREBRAS_SIM_ENVIRONMENT") == "1" else 2)
)
dim = 1 if ph == 1 else 2

nx_max = int(params.get("Nx_max", DEFAULT_MAX_NX))
if args.nx_max is not None:
  nx_max = min(nx_max, args.nx_max)

if nx < 1 or nx > nx_max:
  raise ValueError(f"Nx_start={nx} is outside the supported incremental range 1..{nx_max}")

runner = SdkRuntime(args.name, cmaddr=args.cmaddr)
symbol_time_buf_u16 = runner.get_id("time_buf_u16")
symbol_time_ref = runner.get_id("time_ref")

try:
  runner.load()
  runner.run()

  current_nx = nx
  while current_nx <= nx_max:
    print(
        f"Running {'Allreduce' if is_allred else 'Reduce'} for Pw = {pw}, "
        f"Ph = {ph}, Nx = {current_nx} and algorithm {algo}"
    )

    for _ in range(measurement_repeats):
      print("step 0: sync all PEs")
      runner.launch("f_sync", np.int16(1), nonblock=False)

      print("step 1: prepare (time_start, time_end)")
      runner.launch("f_memcpy_timestamps", nonblock=False)

      print("step 2: D2H (time_start, time_end)")
      time_start, time_end = collect_timestamps(
          runner, symbol_time_buf_u16, symbol_time_ref, pw, ph
      )

      print("DONE!")
      write_result(
          dim,
          algo,
          is_allred,
          current_nx,
          pw,
          ph,
          time_start,
          time_end,
          args.results_file,
          args.csv_file,
      )

    current_nx *= 2
finally:
  runner.stop()
