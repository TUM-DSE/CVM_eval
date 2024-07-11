#!/bin/bash

# Number of repetitions
repeats=10

# snpguest executable path
SNPGUEST="/share/benchmarks/attestation/sev/snpguest/target/release/snpguest"

# Directory for attestation files
ATT_DIR="/root/attestation"
mkdir -p $ATT_DIR

# Certificate types to test
cert_types=("der" "pem")

# Initialize total time arrays
declare -A total_time_report total_time_fetch_ca total_time_fetch_vcek total_time_verify_certs total_time_verify_attestation
# Initialize avg time arrays
declare -A avg_time_report avg_time_fetch_ca avg_time_fetch_vcek avg_time_verify_certs avg_time_verify_attestation

# Function to measure and accumulate time for a command
measure_time() {
    local start_time=$(date +%s%N)
    $@ > /dev/null 2>&1
    local end_time=$(date +%s%N)
    local elapsed=$(( (end_time - start_time) / 1000000 ))
    echo $elapsed
}

# Execute the commands for each certificate type
for cert_type in "${cert_types[@]}"
do      
    # Reset total time variables for each certificate type
    total_time_report[$cert_type]=0
    total_time_fetch_ca[$cert_type]=0
    total_time_fetch_vcek[$cert_type]=0
    total_time_verify_certs[$cert_type]=0
    total_time_verify_attestation[$cert_type]=0

    # Execute the commands $repeats times
    for (( i=1; i<=repeats; i++ ))
    do
        output_report=$(${SNPGUEST} report $ATT_DIR/attestation-report.bin $ATT_DIR/attestation-request-data --random)
        time_report=$(echo "$output_report" | grep "Report generation executed in" | awk '{print $5}')
        total_time_report[$cert_type]=$((total_time_report[$cert_type] + time_report))

        output_fetch_ca=$(${SNPGUEST} fetch ca $cert_type genoa $ATT_DIR/${cert_type}-certs-kds --endorser vcek)
        time_fetch_ca=$(echo "$output_fetch_ca" | grep "Fetch CA executed in" | awk '{print $5}')
        total_time_fetch_ca[$cert_type]=$((total_time_fetch_ca[$cert_type] + time_fetch_ca))

        output_fetch_vcek=$(${SNPGUEST} fetch vcek $cert_type genoa $ATT_DIR/${cert_type}-certs-kds $ATT_DIR/attestation-report.bin)
        time_fetch_vcek=$(echo "$output_fetch_vcek" | grep "CFetch VCEK executed in" | awk '{print $5}')
        total_time_fetch_vcek[$cert_type]=$((total_time_fetch_vcek[$cert_type] + time_fetch_vcek))

        output_verify_certs=$(${SNPGUEST} verify certs $ATT_DIR/${cert_type}-certs-kds)
        time_verify_certs=$(echo "$output_verify_certs" | grep "Verify Certs executed in" | awk '{print $5}')
        total_time_verify_certs[$cert_type]=$((total_time_verify_certs[$cert_type] + time_verify_certs))

        output_verify_attestation=$(${SNPGUEST} verify attestation $ATT_DIR/${cert_type}-certs-kds $ATT_DIR/attestation-report.bin)
        time_verify_attestation=$(echo "$output_verify_attestation" | grep "Verify attestation executed in" | awk '{print $5}')
        total_time_verify_attestation[$cert_type]=$((total_time_verify_attestation[$cert_type] + time_verify_attestation))
        
        # To avoid a potential rate-limit from the AMD service
        sleep 10
    done

    # Calculate average times for each certificate type
    avg_time_report[$cert_type]=$((total_time_report[$cert_type] / repeats))
    avg_time_fetch_ca[$cert_type]=$((total_time_fetch_ca[$cert_type] / repeats))
    avg_time_fetch_vcek[$cert_type]=$((total_time_fetch_vcek[$cert_type] / repeats))
    avg_time_verify_certs[$cert_type]=$((total_time_verify_certs[$cert_type] / repeats))
    avg_time_verify_attestation[$cert_type]=$((total_time_verify_attestation[$cert_type] / repeats))
done

# Print the results in a table format
echo -e "\nAverage Execution Times (in milliseconds) for $repeats repeats:"
printf "%-30s %-10s %-10s\n" "Command" "DER" "PEM"
printf "%-30s %-10s %-10s\n" "-----------------------------" "----------" "----------"
printf "%-30s %-10d %-10d\n" "snpguest report" ${avg_time_report[der]} ${avg_time_report[pem]}
printf "%-30s %-10d %-10d\n" "snpguest fetch ca" ${avg_time_fetch_ca[der]} ${avg_time_fetch_ca[pem]}
printf "%-30s %-10d %-10d\n" "snpguest fetch vcek" ${avg_time_fetch_vcek[der]} ${avg_time_fetch_vcek[pem]}
printf "%-30s %-10d %-10d\n" "snpguest verify certs" ${avg_time_verify_certs[der]} ${avg_time_verify_certs[pem]}
printf "%-30s %-10d %-10d\n" "snpguest verify attestation" ${avg_time_verify_attestation[der]} ${avg_time_verify_attestation[pem]}
