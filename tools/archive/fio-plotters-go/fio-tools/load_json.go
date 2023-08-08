package fio-tools

import (
    "encoding/json"
    "fmt"

    // for MeasurementType
    "github.com/TUM-DSE/CVM_eval/tools/fio-plotters/cli"
    "github.com/TUM-DSE/CVM_eval/tools/fio-plotters/fio-tools/graph"

    "github.com/gonum/plot"
)


func LoadFromJson(pathToJson string, graphType MeasurementType) (paths [string], err error) {

    switch graphType {
    case Bandwidth:
        paths = LoadBWGraph(pathToJson)
    case IOPS:
        paths = LoadIOPSGraph(pathToJson)
    case AverageLatency:
        paths = LoadAverageLatencyGraph(pathToJson)
    default:
        return nil, fmt.Errorf("unrecognized graph type %s", graphType)
    }

    return paths
}


/*
idea: interface type for graphs
each graph has own json loading method / constructor requiring a json
some methods may share certain elements
graph then has a method to plot itself
*/

