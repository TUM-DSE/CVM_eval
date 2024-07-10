#!/bin/bash

THIS_DIR=$(dirname "$(readlink -f "$0")")
ROOT_DIR=$THIS_DIR/../../../

pushd $THIS_DIR > /dev/null

# Number of repetitions
repeats=10

if [ ! -d "go-tdx-guest" ]
then
  git clone https://github.com/google/go-tdx-guest.git > /dev/null 2>&1
fi
# checkout the latest commit as of the time of the writing
cd go-tdx-guest
git checkout f2cf18e98537a20316b8c8d70907eddf4ef5c6be > /dev/null 2>&1
# apply the check.go patch to include the measurements
git apply $THIS_DIR/check.go.patch
# build the tool
cd tools/check/
go build


# Initialize total times for each command
total_quote_verify_remote_pcs=0
total_quote_validate_remote_pcs=0
total_quote_verify_remote_pcs_get_collateral=0
total_validate_remote_pcs_get_collateral=0
# Run the verification the specified number of times
for (( i=0; i<$repeats; i++ ))
do
  output_remote_pcs=$(./check -in $THIS_DIR/quote.dat)
  output_remote_pcs_get_collateral=$(./check -in $THIS_DIR/quote.dat -get_collateral true)

  quote_verify_remote_pcs=$(echo "$output_remote_pcs" | grep "Verify duration" | awk '{print $3}')
  quote_validate_remote_pcs=$(echo "$output_remote_pcs" | grep "Validate duration" | awk '{print $3}')
  quote_verify_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "Verify duration" | awk '{print $3}')
  validate_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "Validate duration" | awk '{print $3}')

  total_quote_verify_remote_pcs=$(echo "$total_quote_verify_remote_pcs + $quote_verify_remote_pcs" | bc)
  total_quote_validate_remote_pcs=$(echo "$total_quote_validate_remote_pcs + $quote_validate_remote_pcs" | bc)
  total_quote_verify_remote_pcs_get_collateral=$(echo "$total_quote_verify_remote_pcs_get_collateral + $quote_verify_remote_pcs_get_collateral" | bc)
  total_validate_remote_pcs_get_collateral=$(echo "$total_validate_remote_pcs_get_collateral + $validate_remote_pcs_get_collateral" | bc)
done

# apply the pcs.go patch to use the local pccs
git apply $THIS_DIR/pcs.go.patch
go build


# Initialize total times for each command
total_quote_verify_local_pcs=0
total_quote_validate_local_pcs=0
total_quote_verify_local_pcs_get_collateral=0
total_validate_local_pcs_get_collateral=0
# Run the verification the specified number of times
for (( i=0; i<$repeats; i++ ))
do
  output_local_pcs=$(./check -in $THIS_DIR/quote.dat)
  output_local_pcs_get_collateral=$(./check -in $THIS_DIR/quote.dat -get_collateral true)

  quote_verify_local_pcs=$(echo "$output_local_pcs" | grep "Verify duration" | awk '{print $3}')
  quote_validate_local_pcs=$(echo "$output_local_pcs" | grep "Validate duration" | awk '{print $3}')
  quote_verify_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "Verify duration" | awk '{print $3}')
  validate_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "Validate duration" | awk '{print $3}')

  total_quote_verify_local_pcs=$(echo "$total_quote_verify_local_pcs + $quote_verify_local_pcs" | bc)
  total_quote_validate_local_pcs=$(echo "$total_quote_validate_local_pcs + $quote_validate_local_pcs" | bc)
  total_quote_verify_local_pcs_get_collateral=$(echo "$total_quote_verify_local_pcs_get_collateral + $quote_verify_local_pcs_get_collateral" | bc)
  total_validate_local_pcs_get_collateral=$(echo "$total_validate_local_pcs_get_collateral + $validate_local_pcs_get_collateral" | bc)
done


# Calculate average times in milliseconds
average_verify_remote_pcs=$(echo "scale=6; $total_quote_verify_remote_pcs / $repeats / 1000000" | bc)
average_validate_remote_pcs=$(echo "scale=6; $total_quote_validate_remote_pcs / $repeats / 1000000" | bc)
average_verify_remote_pcs_get_collateral=$(echo "scale=6; $total_quote_verify_remote_pcs_get_collateral / $repeats / 1000000" | bc)
average_validate_remote_pcs_get_collateral=$(echo "scale=6; $total_validate_remote_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_local_pcs=$(echo "scale=6; $total_quote_verify_local_pcs / $repeats / 1000000" | bc)
average_validate_local_pcs=$(echo "scale=6; $total_quote_validate_local_pcs / $repeats / 1000000" | bc)
average_verify_local_pcs_get_collateral=$(echo "scale=6; $total_quote_verify_local_pcs_get_collateral / $repeats / 1000000" | bc)
average_validate_local_pcs_get_collateral=$(echo "scale=6; $total_validate_local_pcs_get_collateral / $repeats / 1000000" | bc)

# Continue the printing of the results in the existing table format started in measure_attestation.sh
# echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats:"
# printf "%-30s %-10s\n" "Command" "Time (ms)"
# printf "%-30s %-10s\n" "-----------------------------" "----------"
printf "%-50s %-10f\n" "Quote Verify - remote PCS" $average_verify_remote_pcs
printf "%-50s %-10f\n" "Quote Validate - remote PCS" $average_validate_remote_pcs
printf "%-50s %-10f\n" "Quote Verify - remote PCS + collateral" $average_verify_remote_pcs_get_collateral
printf "%-50s %-10f\n" "Quote Validate - remote PCS + collateral" $average_validate_remote_pcs_get_collateral
printf "%-50s %-10f\n" "Quote Verify - local PCS" $average_verify_local_pcs
printf "%-50s %-10f\n" "Quote Validate - local PCS" $average_validate_local_pcs
printf "%-50s %-10f\n" "Quote Verify - local PCS + collateral" $average_verify_local_pcs_get_collateral
printf "%-50s %-10f" "Quote Validate - local PCS + collateral" $average_validate_local_pcs_get_collateral

rm -rf $THIS_DIR/go-tdx-guest $THIS_DIR/quote.dat

popd > /dev/null