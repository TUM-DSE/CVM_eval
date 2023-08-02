package graph

import (
    "fmt"

    // for MeasurementType
    "github.com/TUM-DSE/CVM_eval/tools/fio-plotters/cli"
)


type Graph interface {
    plot() string
}


func LoadGraphFromJson(pathToJson string, graphType MeasurementType) *Graph, err {
    var graph Graph

    switch graphType {
    case Bandwidth:
        graph = LoadBWGraph(pathToJson)
    case IOPS:
        graph = LoadIOPSGraph(pathToJson)
    case AverageLatency:
        graph = LoadAverageLatencyGraph(pathToJson)
    default:
        return nil, fmt.Errorf("unrecognized graph type %s", graphType)
    }

    return graph
}
