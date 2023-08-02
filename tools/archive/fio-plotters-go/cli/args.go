package cli

import (
    "errors"
    "fmt"
    "os"
    "reflect"
    "strings"

    "github.com/urfave/cli/v2"
)

type MeasurementType int

const (
    Bandwidth MeasurementType = iota
    IOPS
    AverageLatency
)

var (
    measurementMap = map[string]MeasurementType{
        "bandwidth": Bandwidth,
        "iops": IOPS,
        "average-latency": AverageLatency,
    }
)

type Args struct {
    InputFile string
    GraphType MeasurementType
}


// arg placement
const requiredArgNum int = 2
const inputFileArgIndex int = 0
const measurementTypeArgIndex int = 1


func ParseArgs() (*Args, error) {
    args := Args{}
    argsUsage := "[INPUT_FILE] ["
    for key, _ := range measurementMap {
        argsUsage += key + "|"
    }
    argsUsage = strings.TrimRight(argsUsage, "|")
    argsUsage += "]"

    app := &cli.App{
        Name: "fio-plotter",
        Usage: "create plots from fio output files",
        ArgsUsage: argsUsage,
        Action: func(cCtx *cli.Context) error {
            if cCtx.NArg() == requiredArgNum {
                args.InputFile = cCtx.Args().Get(inputFileArgIndex)
                if args.InputFile == "" {
                    return errors.New("[INPUT_FILE] may not be empty")
                }
                if _, err := os.Stat(args.InputFile); errors.Is(err, os.ErrNotExist) {
                    return fmt.Errorf("file '%s' does not exist", args.InputFile)
                }
                measurementType, ok := measurementMap[cCtx.Args().Get(measurementTypeArgIndex)]
                if !ok {
                    keys := reflect.ValueOf(measurementMap).MapKeys()
                    return fmt.Errorf("[GRAPH_TYPE] must be of: %s", keys)
                }
                args.GraphType = measurementType
            } else {
                return errors.New(argsUsage)
            }
            return nil
        },
    }

    if err := app.Run(os.Args); err != nil {
        return nil, err
    }

    return &args, nil
}
