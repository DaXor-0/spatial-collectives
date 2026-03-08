import argparse
import csv
import json
import os

import numpy as np

from util import oned_to_hwl_colmajor

from cerebras.sdk.runtime.sdkruntimepybind import SdkRuntime, MemcpyDataType, MemcpyOrder  # pylint: disable=no-name-in-module


MAX_NX = 4096


def make_u48(words):
  return words[0] + (words[1] << 16) + (words[2] << 32)


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


def write_result(dim, algo, is_allred, nx, pw, ph, time_start, time_end):
  elapsed = np.max(time_end) - np.min(time_start)
  start_diff = np.max(time_start) - np.min(time_start)

  with open("results_2d.txt", "a", encoding="utf-8") as result_file:
    result_file.write(
        f"{dim}D, Reduce pattern = {algo}, is allreduce = {is_allred}, "
        f"B = {nx}, Pw = {pw}, Ph = {ph}, time = {elapsed}\n"
    )
    result_file.write(
        f"minimum start = {np.min(time_start)}, maximum start = {np.max(time_start)}, "
        f"diff = {start_diff}\n"
    )

  header = ["Dim", "Pattern", "Allred", "B", "Pw", "Ph", "time", "start_diff"]
  row = [dim, algo, bool(is_allred), nx, pw, ph, elapsed, start_diff]
  with open("data_2d.csv", "a", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    if csv_file.tell() == 0:
      writer.writerow(header)
    writer.writerow(row)


parser = argparse.ArgumentParser()
parser.add_argument("--name", help="the test name")
parser.add_argument("--cmaddr", help="IP:port for CS system")
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

if nx < 1 or nx > MAX_NX:
  raise ValueError(f"Nx_start={nx} is outside the supported incremental range 1..{MAX_NX}")

runner = SdkRuntime(args.name, cmaddr=args.cmaddr)
symbol_time_buf_u16 = runner.get_id("time_buf_u16")
symbol_time_ref = runner.get_id("time_ref")

try:
  runner.load()
  runner.run()

  current_nx = nx
  while current_nx <= MAX_NX:
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
      write_result(dim, algo, is_allred, current_nx, pw, ph, time_start, time_end)

    current_nx *= 2
finally:
  runner.stop()
