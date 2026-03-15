# SDK 1.4.0 Migration Changelog

## Goal

This document records the changes made while migrating this repository from the older Cerebras SDK to SDK `1.4.0`, with emphasis on:

- removing deprecated SDK usage
- restoring WSE-2 compatibility under the new compiler
- adding the queue-bound WSE-3 path where feasible

## 1. Timing API migration

### What changed

- Removed the local time wrapper/module path and switched the kernels to the SDK-provided `<time>` module directly.
- Updated the top-level kernels to import `<time>` instead of the old local module.

### Files

- [code.csl](code.csl)
- [code_pre_order.csl](code_pre_order.csl)
- [code_broadcast.csl](code_broadcast.csl)
- [code_1d_test_inc.csl](code_1d_test_inc.csl)
- [code_1d_pre_order_test.csl](code_1d_pre_order_test.csl)
- [code_2d_test.csl](code_2d_test.csl)
- [code_2d_test_inc.csl](code_2d_test_inc.csl)
- [code_2d_pre_order_test.csl](code_2d_pre_order_test.csl)

### Why

SDK `1.4.0` rejects the older raw config-register access pattern previously used by the local timing implementation. Using `<time>` keeps the timing methodology unchanged while moving timestamp access onto the supported SDK path.

## 2. Architecture guard cleanup

### What changed

- Removed the obsolete `wse1` architecture check.
- Kept the constants module valid for `wse2` and `wse3`.
- Removed the old hardcoded switch-base constants from the shared constants file.

### Files

- [modules/constants.csl](modules/constants.csl)

### Why

SDK `1.4.0` no longer accepts `@is_arch("wse1")`. The repo now asserts against the supported architectures only.

## 3. Config-space access migration

### What changed

- Replaced legacy raw pointer config-register reads and writes with `@get_config` and `@set_config`.
- Updated the color-config helpers to derive color and switch config addresses from `<tile_config>` instead of relying on hardcoded WSE-2-era address math.

### Files

- [modules/wse2_color_config.csl](modules/wse2_color_config.csl)
- [modules/wse2_color_config_with_params.csl](modules/wse2_color_config_with_params.csl)
- [modules/chain_runtime.csl](modules/chain_runtime.csl)
- [modules/2d_chain_runtime.csl](modules/2d_chain_runtime.csl)
- [modules/2d_broadcast_runtime.csl](modules/2d_broadcast_runtime.csl)
- [modules/star_runtime.csl](modules/star_runtime.csl)
- [modules/tree_runtime.csl](modules/tree_runtime.csl)
- [modules/two_phase_runtime.csl](modules/two_phase_runtime.csl)
- [modules/pre_order_runtime_base.csl](modules/pre_order_runtime_base.csl)
- [modules/pre_order_runtime.csl](modules/pre_order_runtime.csl)

### Why

The compiler in SDK `1.4.0` rejects the old direct config-space dereference model. This change moves all supported register access onto the current builtins and makes the address computation architecture-aware.

## 4. Build scripts now pass `--arch`

### What changed

- Added `ARCH="${ARCH:-wse2}"` to the local shell scripts.
- Updated every `cslc` call in those scripts to pass `--arch="$ARCH"`.

### Files

- [commands_1d_fix.sh](commands_1d_fix.sh)
- [commands_1d_pre_order.sh](commands_1d_pre_order.sh)
- [commands_2d_fix.sh](commands_2d_fix.sh)
- [commands_2d_pre_order.sh](commands_2d_pre_order.sh)
- [commands_broadcast.sh](commands_broadcast.sh)
- [commands_inc.sh](commands_inc.sh)

### Why

The SDK examples in `1.4.0` pass architecture explicitly, and the migration work depends on testing separate `wse2` and `wse3` paths. Making the scripts explicit avoids accidental ambiguity.

## 5. WSE-3 launch path migration

### What changed

- Replaced the old color-based `@rpc(@get_data_task_id(sys_mod.LAUNCH))` path with a queue-bound WSE-3 launch path.
- Added a dedicated launch input queue and initialized it under `wse3`.

### Files

- [code.csl](code.csl)
- [code_pre_order.csl](code_pre_order.csl)
- [code_broadcast.csl](code_broadcast.csl)
- [code_1d_test_inc.csl](code_1d_test_inc.csl)
- [code_1d_pre_order_test.csl](code_1d_pre_order_test.csl)
- [code_2d_test.csl](code_2d_test.csl)
- [code_2d_test_inc.csl](code_2d_test_inc.csl)
- [code_2d_pre_order_test.csl](code_2d_pre_order_test.csl)

### Why

On WSE-3, the old color-based launch task binding is no longer accepted. The launch path now matches the queue-bound model expected by the newer SDK.

## 6. Queue-bound fabric DSDs for static collectives

### What changed

- Added explicit WSE-3 `input_queue` and `output_queue` bindings to fabric DSDs in the static collective modules.
- Added queue initialization in `configure_network()` for the WSE-3 path.
- Replaced color-based `@block(...)` with queue-based blocking where needed on WSE-3.
- Parameterized queue IDs per imported module instance to avoid collisions within the same kernel.
- Kept the WSE-2 path on color-only fabric DSDs instead of queue-bound DSDs.

### Files

- [modules/broadcast.csl](modules/broadcast.csl)
- [modules/chain.csl](modules/chain.csl)
- [modules/two_phase.csl](modules/two_phase.csl)
- [modules/tree.csl](modules/tree.csl)
- [modules/two_way_broadcast.csl](modules/two_way_broadcast.csl)
- [modules/star.csl](modules/star.csl)
- [modules/reduce.csl](modules/reduce.csl)

### Why

Under WSE-3, `fabin_dsd` and `fabout_dsd` require explicit queue bindings. The old color-only DSD form compiled on older paths but is rejected by SDK `1.4.0` for WSE-3.
Using queue-bound DSDs on WSE-2 caused post-collective stalls during `memcpy_d2h`, so the repo now selects the DSD form by architecture.

## 7. Queue-bound fabric DSDs for runtime collectives

### What changed

- Added explicit queue parameters to the runtime collective modules.
- Bound all runtime fabric DSDs to queue-backed WSE-3 DSDs.
- For non-preorder runtime paths, reduced queue pressure by making the active queue selection tile-specific at compile time where possible.
- Propagated queue parameters through the runtime wrapper module.
- Kept runtime fabric DSDs color-only on WSE-2 for compatibility with the original receive/blocking model.

### Files

- [modules/chain_runtime.csl](modules/chain_runtime.csl)
- [modules/two_phase_runtime.csl](modules/two_phase_runtime.csl)
- [modules/tree_runtime.csl](modules/tree_runtime.csl)
- [modules/star_runtime.csl](modules/star_runtime.csl)
- [modules/2d_chain_runtime.csl](modules/2d_chain_runtime.csl)
- [modules/2d_broadcast_runtime.csl](modules/2d_broadcast_runtime.csl)
- [modules/reduce_runtime.csl](modules/reduce_runtime.csl)

### Why

The runtime collectives had the same WSE-3 DSD issue as the static path, but they also needed queue allocation that would coexist with `--memcpy`. The non-preorder runtime modules were refactored so each tile initializes only the queue it actually uses.

## 8. Entry-kernel queue allocation

### What changed

- Assigned explicit queue IDs to imported collective instances in the top-level kernels.
- Adjusted the queue map to stay compatible with `--memcpy` on WSE-3.
- Added the missing `reduce.configure_network()` calls in the 1D incremental/pre-order test kernels so runtime queues are initialized before use.

### Files

- [code.csl](code.csl)
- [code_pre_order.csl](code_pre_order.csl)
- [code_broadcast.csl](code_broadcast.csl)
- [code_1d_test_inc.csl](code_1d_test_inc.csl)
- [code_1d_pre_order_test.csl](code_1d_pre_order_test.csl)
- [code_2d_test.csl](code_2d_test.csl)
- [code_2d_test_inc.csl](code_2d_test_inc.csl)
- [code_2d_pre_order_test.csl](code_2d_pre_order_test.csl)

### Why

WSE-3 queue IDs are a finite shared resource, and the memcpy runtime already reserves part of that space. The queue layout had to be made explicit at the kernel level to avoid repeated queue-initialization conflicts.

## 9. 2D tile-coordinate plumbing for WSE-3 queue selection

### What changed

- Added `tile_x` and `tile_y` parameters to the 2D non-preorder entry kernels.
- Passed those coordinates from the corresponding layout files.
- Used those coordinates in `2d_chain_runtime` to select the active queue at compile time.

### Files

- [layout_2d_test.csl](layout_2d_test.csl)
- [layout_2d_test_inc.csl](layout_2d_test_inc.csl)
- [layout_2d_pre_order_test.csl](layout_2d_pre_order_test.csl)
- [code_2d_test.csl](code_2d_test.csl)
- [code_2d_test_inc.csl](code_2d_test_inc.csl)
- [code_2d_pre_order_test.csl](code_2d_pre_order_test.csl)
- [modules/2d_chain_runtime.csl](modules/2d_chain_runtime.csl)

### Why

Without compile-time tile coordinates, the 2D runtime path had to reserve queues for both colors on every tile, which collided with the memcpy runtime. The coordinate plumbing lets the non-preorder 2D path bind only the queue a tile actually needs.

## 10. Pre-order generator synchronization

### What changed

- Updated the pre-order base file to keep the same SDK migration changes as the generated file.
- Updated the generator to insert generated per-PE state relative to a stable anchor instead of a brittle fixed line number.

### Files

- [modules/pre_order_runtime_base.csl](modules/pre_order_runtime_base.csl)
- [modules/pre_order_runtime.csl](modules/pre_order_runtime.csl)
- [generate_pre_order_2d.py](generate_pre_order_2d.py)

### Why

The generated pre-order runtime is recreated from the base/template flow. Migration fixes had to live in the source path as well, otherwise regeneration would reintroduce old code.

## 11. Static 1D parameter-name alignment

### What changed

- Fixed the static 1D build script to pass `Nx` instead of the obsolete `Nx_start`.
- Removed the unused `Ph` parameter from that same invocation.
- Updated the Python reduce/allreduce runners to accept either `Nx` or `Nx_start`, and to default `Ph` to `1` when it is omitted by 1D builds.

### Files

- [commands_1d_fix.sh](commands_1d_fix.sh)
- [run_2d_test.py](run_2d_test.py)
- [run_2d_specific_pe_test.py](run_2d_specific_pe_test.py)

### Why

The static 1D layout expects `Nx`, not `Nx_start`, and does not require `Ph`. The shared Python runners were still assuming the older parameter shape from the 2D path, which would break once the shell script was corrected. The fallback logic keeps the runners compatible with both compile outputs.

## 12. Simulation repeat-count override

### What changed

- The Python measurement runners now reduce their per-case measurement loop from `5` to `1` when `CEREBRAS_SIM_ENVIRONMENT=1`.
- The kernels that use an internal repeat threshold now take that threshold as a compile parameter instead of hardcoding `5`.
- The shell entrypoints that compile those kernels now pass `repeats:1` when `CEREBRAS_SIM_ENVIRONMENT=1`, otherwise they keep `repeats:5`.
- The broadcast shell script now reduces its outer shell repeat loop to `1` under the same environment variable.

### Files

- [run_2d_test.py](run_2d_test.py)
- [run_2d_specific_pe_test.py](run_2d_specific_pe_test.py)
- [code_1d_test_inc.csl](code_1d_test_inc.csl)
- [code_1d_pre_order_test.csl](code_1d_pre_order_test.csl)
- [code_2d_test.csl](code_2d_test.csl)
- [code_2d_test_inc.csl](code_2d_test_inc.csl)
- [code_2d_pre_order_test.csl](code_2d_pre_order_test.csl)
- [layout_1d_test_inc.csl](layout_1d_test_inc.csl)
- [layout_1d_pre_order_test.csl](layout_1d_pre_order_test.csl)
- [layout_2d_test.csl](layout_2d_test.csl)
- [layout_2d_test_inc.csl](layout_2d_test_inc.csl)
- [layout_2d_pre_order_test.csl](layout_2d_pre_order_test.csl)
- [commands_1d_pre_order.sh](commands_1d_pre_order.sh)
- [commands_2d_fix.sh](commands_2d_fix.sh)
- [commands_2d_pre_order.sh](commands_2d_pre_order.sh)
- [commands_inc.sh](commands_inc.sh)
- [commands_broadcast.sh](commands_broadcast.sh)

### Why

Simulation runs do not need the same repetition count as hardware runs, and keeping the count at `5` slows verification unnecessarily. The override keeps the runner-side loops and the kernel-side repeat threshold aligned so the measurement phases still advance correctly under simulation.

## Validation status

The following representative WSE-3 compiles now succeed:

- [layout.csl](layout.csl)
- [layout_1d_test_inc.csl](layout_1d_test_inc.csl)
- [layout_broadcast.csl](layout_broadcast.csl)
- [layout_2d_test.csl](layout_2d_test.csl)

These validations confirm that the main non-preorder WSE-3 queue-bound path is working under SDK `1.4.0`.

## Known remaining issues

- The pre-order WSE-3 path is still incomplete.
  - [layout_1d_pre_order_test.csl](layout_1d_pre_order_test.csl) currently fails in the compiler/backend with a route-setting assertion.
  - [layout_2d_pre_order_test.csl](layout_2d_pre_order_test.csl) still has queue-pressure issues because the pre-order runtime path still needs two active colors per instance.

## 13. Incremental `Nx` sweep restoration

### What changed

- Restored `commands_inc.sh` to start from a real runtime sweep seed, `Nx_start`, instead of hardcoding `1`.
- Split the incremental path into separate reduce and allreduce builds, matching the non-incremental scripts instead of relying on a kernel-side mode switch.
- Added a dedicated incremental runner that logs the compile-selected collective type and advances `B` until the fixed `x[4096]` buffer limit.
- Restored the incremental kernels so they advance `Nx` after each measurement batch and use the compile-time `is_allred` parameter only for collective selection.
- Reduced the incremental default measurement batch size to `2`, while keeping the existing `CEREBRAS_SIM_ENVIRONMENT=1` override at `1`.
- Updated the SLURM incremental entrypoint to use the same flow.

### Files

- [commands_inc.sh](commands_inc.sh)
- [cmds_inc_cs_new.slurm](cmds_inc_cs_new.slurm)
- [code_1d_test_inc.csl](code_1d_test_inc.csl)
- [code_2d_test_inc.csl](code_2d_test_inc.csl)
- [run_inc_test.py](run_inc_test.py)

### Why

The incremental path had drifted into an inconsistent state:

- the shell script compiled with `Nx_start:1`
- the kernels no longer advanced `Nx`
- the host runner mislabeled a second measurement phase as allreduce even though the compiled binary was still reduce-only

That combination made `B` appear constant or misleading. The incremental path now behaves as intended again: PE count is fixed at compile time, while `B` changes at runtime across measurement batches.

## 14. CSV algorithm labels

### What changed

- Added an `Algorithm` column to the CSV outputs written by the measurement runners.
- Kept the numeric `Pattern` column and added a string label alongside it.
- Standardized the mapping across runners:
  - `0 -> chain`
  - `1 -> two_phase`
  - `2 -> tree`
  - `3 -> star`
  - `4 -> bine`

### Files

- [run_2d_test.py](run_2d_test.py)
- [run_inc_test.py](run_inc_test.py)
- [run_2d_specific_pe_test.py](run_2d_specific_pe_test.py)
- [run_bcast.py](run_bcast.py)

### Why

The numeric `Pattern` field alone made the CSV output harder to read and compare across runs. Adding the algorithm name makes the collected data self-describing without removing the original numeric identifier.

## 15. `bine` 1D collective integration

### What changed

- Added a dedicated 1D `bine` layout and top-level kernel so the copied collective can be compiled and measured through the repo’s existing infrastructure.
- Added a dedicated `bine` reduce module.
- Wired algorithm `4` in the 1D static shell entrypoint to compile the `bine` layout instead of the default `layout.csl`.
- Kept the `bine` allreduce split at the top level:
  - `bine.transfer_data(...)` performs the staged reduce phase only
  - the top-level kernel uses the existing `is_allred` gate
  - the allreduce completion path is handled separately from the reduce module

### Files

- [layout_bine.csl](layout_bine.csl)
- [code_bine.csl](code_bine.csl)
- [modules/bine.csl](modules/bine.csl)
- [modules/broadcast_rooted.csl](modules/broadcast_rooted.csl)
- [commands_1d_fix.sh](commands_1d_fix.sh)
- [run_2d_test.py](run_2d_test.py)
- [run_inc_test.py](run_inc_test.py)
- [run_2d_specific_pe_test.py](run_2d_specific_pe_test.py)
- [run_bcast.py](run_bcast.py)

### Why

The copied `bine` code in `bine/` was a standalone program with its own layout and allreduce path, so it did not fit directly into the repository’s `layout/code/module/run` structure.

The integration work isolates the `bine` reduce network in its own module and keeps the allreduce decision in the top-level kernel so it can be measured through the same runners and CSV outputs as the existing algorithms.

## 16. `bine` incremental 1D integration

### What changed

- Added a dedicated incremental `bine` kernel and layout so `commands_inc.sh` can run algorithm `4`.
- Kept the same runtime `B` growth model as the other incremental kernels:
  - `Nx` starts from `Nx_start`
  - `Nx` doubles at runtime after each measurement batch
  - `Nx` is capped by a compile-time `Nx_max` parameter
- Kept the `bine` allreduce split at the top level:
  - `bine.transfer_data(...)` performs the reduce phase
  - the top-level kernel checks `is_allred`
  - the allreduce completion path is handled separately from the reduce module
- Updated `commands_inc.sh` so it compiles `layout_bine_inc.csl` when `algo == 4`.
- Added a dedicated `BINE_NX_MAX` shell parameter, defaulting to `2048`, because
  `bine` needs two extra `max_count` scratch buffers and does not fit at the
  generic `4096` incremental cap.

### Files

- [code_bine_inc.csl](code_bine_inc.csl)
- [layout_bine_inc.csl](layout_bine_inc.csl)
- [commands_inc.sh](commands_inc.sh)
- [run_inc_test.py](run_inc_test.py)
- [code_bine.csl](code_bine.csl)

### Why

The existing incremental 1D path compiles `layout_1d_test_inc.csl`, whose kernel dispatches `algo >= 3` to `star`. That means `Algo:4` could not select `bine`, even though the static 1D path already supported it.

Adding a dedicated incremental `bine` path keeps the repository structure consistent:

- static 1D `bine` uses `layout_bine.csl` and `code_bine.csl`
- incremental 1D `bine` now uses `layout_bine_inc.csl` and `code_bine_inc.csl`

This makes `commands_inc.sh` able to measure `bine` without changing the meaning of the existing incremental kernels, while keeping the `bine` memory footprint within the PE-local memory budget.

### Follow-up: original `bine` allreduce root

The staged `bine` path now uses the original nonzero root selection from the
copied `bine/` program for its allreduce phase, rather than forcing the result
through the repo's PE0-root `broadcast_right` path.

Files changed:

- [code_bine.csl](code_bine.csl)
- [code_bine_inc.csl](code_bine_inc.csl)
- [layout_bine.csl](layout_bine.csl)
- [layout_bine_inc.csl](layout_bine_inc.csl)
- [modules/broadcast_rooted.csl](modules/broadcast_rooted.csl)

What changed:

- restored the original `bine` root computation
- added a dedicated rooted 1D broadcast module for the allreduce phase
- changed staged-`bine` completion so allreduce broadcasts from the original `bine` root
- moved the sync callback task ids away from the rooted-broadcast color ids to avoid runtime aliasing

Why:

The original `bine` code does not reduce to `PE 0`; it reduces to a schedule-
dependent root and then broadcasts from that root. The staged `bine` integration
now matches that behavior for allreduce without consuming the extra queue space
required by `<collectives_2d>`.

## 17. `bine_new` streaming 1D variant

### What changed

- Added a new algorithm `5`, named `bine_new`.
- Added a dedicated streaming reduce module with no full-message receive scratch buffers.
- Added dedicated static and incremental 1D kernels/layouts for `bine_new`.
- Wired `bine_new` into the shell entrypoints and CSV algorithm-name maps.

### Files

- [modules/bine_new.csl](modules/bine_new.csl)
- [code_bine_new.csl](code_bine_new.csl)
- [layout_bine_new.csl](layout_bine_new.csl)
- [code_bine_new_inc.csl](code_bine_new_inc.csl)
- [layout_bine_new_inc.csl](layout_bine_new_inc.csl)
- [commands_1d_fix.sh](commands_1d_fix.sh)
- [commands_inc.sh](commands_inc.sh)
- [run_2d_test.py](run_2d_test.py)
- [run_inc_test.py](run_inc_test.py)
- [run_2d_specific_pe_test.py](run_2d_specific_pe_test.py)
- [run_bcast.py](run_bcast.py)

### Why

The original integrated `bine` algorithm stages inbound payloads in two `max_count`
scratch buffers before forwarding or reducing them. That increases the per-PE memory
footprint and forces a lower incremental `Nx_max`.

`bine_new` is a separate PE0-root streaming variant that uses direct fabric DSDs in
the same style as the built-in streaming collectives. This keeps the existing `bine`
algorithm available while adding a no-scratch alternative that fits the repo's
current 1D allreduce infrastructure.

## 18. Allreduce-only 1D benchmark with original `bine`

### What changed

- Added a dedicated allreduce-only benchmark script for the 1D collectives.
- Kept algorithms `0..3` on the existing incremental allreduce path and capped the host-side sweep to `Nx = 2048`.
- Added a dedicated timed benchmark variant of the original standalone `bine` program.
- Added a dedicated runner for the original `bine` benchmark that recompiles per `(Pw, Nx)`, reinitializes per-PE input buffers, and starts the H2D loop from the original `bine` root.
- Added optional output-file and `Nx` cap arguments to the shared incremental runner so benchmark data can be written to a dedicated CSV/results pair.
- Added a `total_time` reporting path for the native-collective runners so benchmark output can include both corrected collective time and synchronization-plus-collective time.
- Finalized the standalone `bine` benchmark to report root-local total time only, rather than trying to reuse the native-collective synchronization correction path.
- Adjusted the standalone `bine` benchmark PE program so tiles that relay a later reduction message do not enter the final broadcast too early.

### Files

- [commands_allreduce_benchmark.sh](commands_allreduce_benchmark.sh)
- [bine/benchmark_layout.csl](bine/benchmark_layout.csl)
- [bine/benchmark_pe.csl](bine/benchmark_pe.csl)
- [bine/benchmark_run.py](bine/benchmark_run.py)
- [run_inc_test.py](run_inc_test.py)
- [run_2d_test.py](run_2d_test.py)
- [run_2d_specific_pe_test.py](run_2d_specific_pe_test.py)

### Why

The existing incremental script mixes reduce and allreduce and uses the integrated staged `bine`, which is still not valid beyond `Pw = 4`. The original standalone `bine/` program does work beyond `4` PEs, but it needs its own benchmark path because:

- it is an allreduce, not a split reduce/allreduce path
- it uses a nonzero root
- it is most reliable when left in its standalone structure and recompiled per benchmarked `(Pw, Nx)` pair
- it does not share the same start-time correction machinery as the native incremental collectives
- some tiles participate in the original staged reduction as relays after their first send, so the benchmark variant must delay their `completed()` callback until that relay step finishes

The new benchmark script measures:

- `Pw = 4, 8, 16, 32, 64`
- `Nx = 1, 2, 4, ..., 2048`
- allreduce only
- algorithms `chain`, `two_phase`, `tree`, `star`, and `bine_original`

For the reported timings:

- native collectives now write both `time` and `total_time`, where `time` is the corrected collective window and `total_time` includes the synchronization delay plus the collective
- the original standalone `bine` benchmark writes only root-local total time in practice; its CSV row stores that value in both `time` and `total_time` so the benchmark CSV remains rectangular

The benchmark-specific `bine` PE program also avoids the original payload-growth stall by:

- stopping the staged reduction before the extra final dissemination step
- using the `collectives_2d` rooted broadcast for the allreduce fanout
- delaying `completed()` on relay tiles that still need to forward one later reduction message
