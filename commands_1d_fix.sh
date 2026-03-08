#!/usr/bin/env bash
# set -e
# 1D Reduce and Allreduce

ARCH="${ARCH:-wse2}"
MEASUREMENT_REPEATS=5
: "${CEREBRAS_SIM_ENVIRONMENT:=1}"
export CEREBRAS_SIM_ENVIRONMENT
if [ "${CEREBRAS_SIM_ENVIRONMENT}" = "1" ]; then
  MEASUREMENT_REPEATS=1
fi

for algo in {0..3}
do
  sqrt_result=$(echo "sqrt(32)" | bc -l)
  int_result=${sqrt_result%.*}
  cslc layout.csl --arch="$ARCH" --fabric-dims=39,3 \
  --fabric-offsets=4,1 --params=Nx:1,Pw:32,Algo:$algo,is_allred:0,step:$int_result -o out --memcpy --channels=1
  CEREBRAS_SIM_ENVIRONMENT="$CEREBRAS_SIM_ENVIRONMENT" cs_python run_2d_test.py --name out
done

for algo in {0..3}
do
  sqrt_result=$(echo "sqrt(32)" | bc -l)
  int_result=${sqrt_result%.*}
  cslc layout.csl --arch="$ARCH" --fabric-dims=39,3 \
  --fabric-offsets=4,1 --params=Nx:1,Pw:32,Algo:$algo,is_allred:1,step:$int_result -o out --memcpy --channels=1
  CEREBRAS_SIM_ENVIRONMENT="$CEREBRAS_SIM_ENVIRONMENT" cs_python run_2d_test.py --name out
done
