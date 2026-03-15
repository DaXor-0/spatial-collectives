#!/usr/bin/env bash
set -e

ARCH="${ARCH:-wse2}"
NX_START="${NX_START:-1}"
NX_MAX="${NX_MAX:-2048}"
MEASUREMENT_REPEATS=1
RESULTS_FILE="${RESULTS_FILE:-results_allreduce_1d.txt}"
CSV_FILE="${CSV_FILE:-data_allreduce_1d.csv}"

: "${CEREBRAS_SIM_ENVIRONMENT:=1}"
export CEREBRAS_SIM_ENVIRONMENT
if [ "${CEREBRAS_SIM_ENVIRONMENT}" = "1" ]; then
  MEASUREMENT_REPEATS=1
fi


# for log_pes in {2..6}
# do
#   pw=$((2**log_pes))
#   nx=$NX_START
#   while [ "$nx" -le "$NX_MAX" ]
#   do
#     cslc bine/benchmark_layout.csl --arch="$ARCH" --fabric-dims=71,3 \
#       --fabric-offsets=4,1 \
#       --params="len:$nx,dim_lay:$pw" \
#       -o out --memcpy --channels=1
#     CEREBRAS_SIM_ENVIRONMENT="$CEREBRAS_SIM_ENVIRONMENT" cs_python bine/benchmark_run.py \
#       --name out \
#       --results-file "$RESULTS_FILE" \
#       --csv-file "$CSV_FILE" \
#       --measurement-repeats "$MEASUREMENT_REPEATS"
#     nx=$((nx * 2))
#   done
# done


for algo in 0 1 2 3
do
  for log_pes in {2..4}
  do
    pw=$((2**log_pes))
    sqrt_result=$(echo "sqrt($pw)" | bc -l)
    int_result=${sqrt_result%.*}
    cslc layout_1d_test_inc.csl --arch="$ARCH" --fabric-dims=71,3 \
      --fabric-offsets=4,1 \
      --params="Nx_start:$NX_START,Pw:$pw,Ph:1,Algo:$algo,is_allred:1,step:$int_result,repeats:$MEASUREMENT_REPEATS" \
      -o out --memcpy --channels=1
    CEREBRAS_SIM_ENVIRONMENT="$CEREBRAS_SIM_ENVIRONMENT" cs_python run_inc_test.py \
      --name out \
      --results-file "$RESULTS_FILE" \
      --csv-file "$CSV_FILE" \
      --nx-max "$NX_MAX"
  done
done


