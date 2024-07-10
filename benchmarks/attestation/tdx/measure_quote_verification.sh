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
# apply the go-tdx-guest-measurements.patch patch to include the measurements
git apply $THIS_DIR/go-tdx-guest-measurements.patch
# build the tool
cd tools/check/
go build


# Initialize total times for each command
total_retrieving_collateral_remote_pcs=0
total_verify_PCK_remote_pcs=0
total_verify_quote_remote_pcs=0
total_verify_remote_pcs=0
total_validate_remote_pcs=0

total_retrieving_collateral_remote_pcs_get_collateral=0
total_verify_PCK_remote_pcs_get_collateral=0
total_verify_quote_remote_pcs_get_collateral=0
total_verify_remote_pcs_get_collateral=0
total_validate_remote_pcs_get_collateral=0
# Run the verification the specified number of times
for (( i=0; i<$repeats; i++ ))
do
  output_remote_pcs=$(./check -in $THIS_DIR/quote.dat)
  output_remote_pcs_get_collateral=$(./check -in $THIS_DIR/quote.dat -get_collateral true)

  retrieving_collateral_remote_pcs=$(echo "$output_remote_pcs" | grep "Retrieving Collateral duration" | awk '{print $4}')
  verify_PCK_remote_pcs=$(echo "$output_remote_pcs" | grep "Verify PCK duration" | awk '{print $4}')
  verify_quote_remote_pcs=$(echo "$output_remote_pcs" | grep "Verify Quote duration" | awk '{print $4}')
  verify_remote_pcs=$(echo "$output_remote_pcs" | grep "End-to-end Verify duration" | awk '{print $4}')
  validate_remote_pcs=$(echo "$output_remote_pcs" | grep "Validate duration" | awk '{print $3}')

  retrieving_collateral_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "Retrieving Collateral duration" | awk '{print $4}')
  verify_PCK_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "Verify PCK duration" | awk '{print $4}')
  verify_quote_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "Verify Quote duration" | awk '{print $4}')
  verify_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "End-to-end Verify duration" | awk '{print $4}')
  validate_remote_pcs_get_collateral=$(echo "$output_remote_pcs_get_collateral" | grep "Validate duration" | awk '{print $3}')

  total_retrieving_collateral_remote_pcs=$(echo "$total_retrieving_collateral_remote_pcs + $retrieving_collateral_remote_pcs" | bc)
  total_verify_PCK_remote_pcs=$(echo "$total_verify_PCK_remote_pcs + $verify_PCK_remote_pcs" | bc)
  total_verify_quote_remote_pcs=$(echo "$total_verify_quote_remote_pcs + $verify_quote_remote_pcs" | bc)
  total_verify_remote_pcs=$(echo "$total_verify_remote_pcs + $verify_remote_pcs" | bc)
  total_validate_remote_pcs=$(echo "$total_validate_remote_pcs + $validate_remote_pcs" | bc)
  
  total_retrieving_collateral_remote_pcs_get_collateral=$(echo "$total_retrieving_collateral_remote_pcs_get_collateral + $retrieving_collateral_remote_pcs_get_collateral" | bc)
  total_verify_PCK_remote_pcs_get_collateral=$(echo "$total_verify_PCK_remote_pcs_get_collateral + $verify_PCK_remote_pcs_get_collateral" | bc)
  total_verify_quote_remote_pcs_get_collateral=$(echo "$total_verify_quote_remote_pcs_get_collateral + $verify_quote_remote_pcs_get_collateral" | bc)
  total_verify_remote_pcs_get_collateral=$(echo "$total_verify_remote_pcs_get_collateral + $verify_remote_pcs_get_collateral" | bc)
  total_validate_remote_pcs_get_collateral=$(echo "$total_validate_remote_pcs_get_collateral + $validate_remote_pcs_get_collateral" | bc)
done

# apply the pcs.go patch to use the local pccs
git apply $THIS_DIR/pcs.go.patch
go build

# Initialize total times for each command
total_retrieving_collateral_local_pcs=0
total_verify_PCK_local_pcs=0
total_verify_quote_local_pcs=0
total_verify_local_pcs=0
total_validate_local_pcs=0

total_retrieving_collateral_local_pcs_get_collateral=0
total_verify_PCK_local_pcs_get_collateral=0
total_verify_quote_local_pcs_get_collateral=0
total_verify_local_pcs_get_collateral=0
total_validate_local_pcs_get_collateral=0
# Run the verification the specified number of times
for (( i=0; i<$repeats; i++ ))
do
  output_local_pcs=$(./check -in $THIS_DIR/quote.dat)
  output_local_pcs_get_collateral=$(./check -in $THIS_DIR/quote.dat -get_collateral true)

  retrieving_collateral_local_pcs=$(echo "$output_local_pcs" | grep "Retrieving Collateral duration" | awk '{print $4}')
  verify_PCK_local_pcs=$(echo "$output_local_pcs" | grep "Verify PCK duration" | awk '{print $4}')
  verify_quote_local_pcs=$(echo "$output_local_pcs" | grep "Verify Quote duration" | awk '{print $4}')
  verify_local_pcs=$(echo "$output_local_pcs" | grep "End-to-end Verify duration" | awk '{print $4}')
  validate_local_pcs=$(echo "$output_local_pcs" | grep "Validate duration" | awk '{print $3}')

  retrieving_collateral_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "Retrieving Collateral duration" | awk '{print $4}')
  verify_PCK_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "Verify PCK duration" | awk '{print $4}')
  verify_quote_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "Verify Quote duration" | awk '{print $4}')
  verify_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "End-to-end Verify duration" | awk '{print $4}')
  validate_local_pcs_get_collateral=$(echo "$output_local_pcs_get_collateral" | grep "Validate duration" | awk '{print $3}')

  total_retrieving_collateral_local_pcs=$(echo "$total_retrieving_collateral_local_pcs + $retrieving_collateral_local_pcs" | bc)
  total_verify_PCK_local_pcs=$(echo "$total_verify_PCK_local_pcs + $verify_PCK_local_pcs" | bc)
  total_verify_quote_local_pcs=$(echo "$total_verify_quote_local_pcs + $verify_quote_local_pcs" | bc)
  total_verify_local_pcs=$(echo "$total_verify_local_pcs + $verify_local_pcs" | bc)
  total_validate_local_pcs=$(echo "$total_validate_local_pcs + $validate_local_pcs" | bc)

  total_retrieving_collateral_local_pcs_get_collateral=$(echo "$total_retrieving_collateral_local_pcs_get_collateral + $retrieving_collateral_local_pcs_get_collateral" | bc)
  total_verify_PCK_local_pcs_get_collateral=$(echo "$total_verify_PCK_local_pcs_get_collateral + $verify_PCK_local_pcs_get_collateral" | bc)
  total_verify_quote_local_pcs_get_collateral=$(echo "$total_verify_quote_local_pcs_get_collateral + $verify_quote_local_pcs_get_collateral" | bc)
  total_verify_local_pcs_get_collateral=$(echo "$total_verify_local_pcs_get_collateral + $verify_local_pcs_get_collateral" | bc)
  total_validate_local_pcs_get_collateral=$(echo "$total_validate_local_pcs_get_collateral + $validate_local_pcs_get_collateral" | bc)
done


# Calculate average times in milliseconds
average_retrieving_collateral_remote_pcs=$(echo "scale=6; $total_retrieving_collateral_remote_pcs / $repeats / 1000000" | bc)
average_verify_PCK_remote_pcs=$(echo "scale=6; $total_verify_PCK_remote_pcs / $repeats / 1000000" | bc)
average_verify_quote_remote_pcs=$(echo "scale=6; $total_verify_quote_remote_pcs / $repeats / 1000000" | bc)
average_verify_remote_pcs=$(echo "scale=6; $total_verify_remote_pcs / $repeats / 1000000" | bc)
average_validate_remote_pcs=$(echo "scale=6; $total_validate_remote_pcs / $repeats / 1000000" | bc)

average_retrieving_collateral_remote_pcs_get_collateral=$(echo "scale=6; $total_retrieving_collateral_remote_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_PCK_remote_pcs_get_collateral=$(echo "scale=6; $total_verify_PCK_remote_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_quote_remote_pcs_get_collateral=$(echo "scale=6; $total_verify_quote_remote_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_remote_pcs_get_collateral=$(echo "scale=6; $total_verify_remote_pcs_get_collateral / $repeats / 1000000" | bc)
average_validate_remote_pcs_get_collateral=$(echo "scale=6; $total_validate_remote_pcs_get_collateral / $repeats / 1000000" | bc)

average_retrieving_collateral_local_pcs=$(echo "scale=6; $total_retrieving_collateral_local_pcs / $repeats / 1000000" | bc)
average_verify_PCK_local_pcs=$(echo "scale=6; $total_verify_PCK_local_pcs / $repeats / 1000000" | bc)
average_verify_quote_local_pcs=$(echo "scale=6; $total_verify_quote_local_pcs / $repeats / 1000000" | bc)
average_verify_local_pcs=$(echo "scale=6; $total_verify_local_pcs / $repeats / 1000000" | bc)
average_validate_local_pcs=$(echo "scale=6; $total_validate_local_pcs / $repeats / 1000000" | bc)

average_retrieving_collateral_local_pcs_get_collateral=$(echo "scale=6; $total_retrieving_collateral_local_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_PCK_local_pcs_get_collateral=$(echo "scale=6; $total_verify_PCK_local_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_quote_local_pcs_get_collateral=$(echo "scale=6; $total_verify_quote_local_pcs_get_collateral / $repeats / 1000000" | bc)
average_verify_local_pcs_get_collateral=$(echo "scale=6; $total_verify_local_pcs_get_collateral / $repeats / 1000000" | bc)
average_validate_local_pcs_get_collateral=$(echo "scale=6; $total_validate_local_pcs_get_collateral / $repeats / 1000000" | bc)

# Continue the printing of the results in the existing table format started in measure_attestation.sh
echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats for remote PCS:"
printf "%-50s %-10s\n" "Command" "Time (ms)"
printf "%-50s %-10s\n" "---------------------------------------" "----------"
printf "%-50s %-10f\n" "Rertieving Collateral" $average_retrieving_collateral_remote_pcs
printf "%-50s %-10f\n" "Verify PCK" $average_verify_PCK_remote_pcs
printf "%-50s %-10f\n" "Verify Quote" $average_verify_quote_remote_pcs
printf "%-50s %-10f\n" "End-to-end Verify" $average_verify_remote_pcs
printf "%-50s %-10f\n" "Quote Validate" $average_validate_remote_pcs

echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats for remote PCS with Collateral fetching:"
printf "%-50s %-10s\n" "Command" "Time (ms)"
printf "%-50s %-10s\n" "---------------------------------------" "----------"
printf "%-50s %-10f\n" "Rertieving collateral" $average_retrieving_collateral_remote_pcs_get_collateral
printf "%-50s %-10f\n" "Verify PCK" $average_verify_PCK_remote_pcs_get_collateral
printf "%-50s %-10f\n" "Verify Quote" $average_verify_quote_remote_pcs_get_collateral
printf "%-50s %-10f\n" "End-to-end Verify" $average_verify_remote_pcs_get_collateral
printf "%-50s %-10f\n" "Quote Validate" $average_validate_remote_pcs_get_collateral

echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats for local PCS:"
printf "%-50s %-10s\n" "Command" "Time (ms)"
printf "%-50s %-10s\n" "---------------------------------------" "----------"
printf "%-50s %-10f\n" "Rertieving Collateral" $average_retrieving_collateral_local_pcs
printf "%-50s %-10f\n" "Verify PCK" $average_verify_PCK_local_pcs
printf "%-50s %-10f\n" "Verify Quote" $average_verify_quote_local_pcs
printf "%-50s %-10f\n" "End-to-end Verify" $average_verify_local_pcs
printf "%-50s %-10f\n" "Quote Validate" $average_validate_local_pcs

echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats for local PCS with Collateral fetching:"
printf "%-50s %-10s\n" "Command" "Time (ms)"
printf "%-50s %-10s\n" "---------------------------------------" "----------"
printf "%-50s %-10f\n" "Rertieving Collateral" $average_retrieving_collateral_local_pcs_get_collateral
printf "%-50s %-10f\n" "Verify PCK" $average_verify_PCK_local_pcs_get_collateral
printf "%-50s %-10f\n" "Verify Quote" $average_verify_quote_local_pcs_get_collateral
printf "%-50s %-10f\n" "End-to-end Verify" $average_verify_local_pcs_get_collateral
printf "%-50s %-10f\n" "Quote Validate" $average_validate_local_pcs_get_collateral

rm -rf $THIS_DIR/go-tdx-guest $THIS_DIR/quote.dat

popd > /dev/null