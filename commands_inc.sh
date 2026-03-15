#!/usr/bin/env bash
# set -e

ARCH="${ARCH:-wse2}"
NX_START="${NX_START:-1}"
BINE_NX_MAX="${BINE_NX_MAX:-2048}"
MEASUREMENT_REPEATS=5
: "${CEREBRAS_SIM_ENVIRONMENT:=1}"
export CEREBRAS_SIM_ENVIRONMENT
if [ "${CEREBRAS_SIM_ENVIRONMENT}" = "1" ]; then
  MEASUREMENT_REPEATS=1
fi

# 1D Reduce and Allreduce
for is_allred in 0 1
do
  for algo in {0..4}
  do
    for log_pes in {2..6}
    do
      sqrt_result=$(echo "sqrt(2^$log_pes)" | bc -l)
      int_result=${sqrt_result%.*}
      layout_file="layout_1d_test_inc.csl"
      params="Nx_start:$NX_START,Pw:$((2**$log_pes)),Ph:1,Algo:$algo,is_allred:$is_allred,step:$int_result,repeats:$MEASUREMENT_REPEATS"
      if [ "$algo" -eq 4 ]; then
        layout_file="layout_bine_inc.csl"
        params="$params,Nx_max:$BINE_NX_MAX"
      fi
      cslc "$layout_file" --arch="$ARCH" --fabric-dims=71,3 \
      --fabric-offsets=4,1 --params="$params" -o out --memcpy --channels=1
      CEREBRAS_SIM_ENVIRONMENT="$CEREBRAS_SIM_ENVIRONMENT" cs_python run_inc_test.py --name out
    done
  done
done

# 2D Reduce and Allreduce
# for is_allred in 0 1
# do
#   for algo in {0..3}
#   do
#     for log_pes in {2..8}
#     do
#       sqrt_result=$(echo "sqrt(2^$log_pes)" | bc -l)
#       int_result=${sqrt_result%.*}
#       cslc layout_2d_test_inc.csl --arch="$ARCH" --fabric-dims=519,514 \
#       --fabric-offsets=4,1 --params=Nx_start:$NX_START,Pw:$((2**$log_pes)),Ph:$((2**$log_pes)),Algo:$algo,is_allred:$is_allred,step:$int_result,repeats:$MEASUREMENT_REPEATS -o out --memcpy --channels=1
#       CEREBRAS_SIM_ENVIRONMENT="$CEREBRAS_SIM_ENVIRONMENT" cs_python run_inc_test.py --name out
#     done
#   done
# done
