package main

import (
    "fmt"
    "os"

    "github.com/TUM-DSE/CVM_eval/tools/fio-plotters/cli"
    "github.com/TUM-DSE/CVM_eval/tools/fio-plotters/fio-tools"
)

func main() {
    args, err := cli.ParseArgs()
    if err != nil {
            fmt.Printf("failed to parse args: %v\n", err)
            os.Exit(1)
    }

    fmt.Printf("got args: ", args)
}
