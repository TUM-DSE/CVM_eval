package graph

import (
    "os"

    "encoding/json"
)

type BWGraph struct {}

func LoadBWGraph(pathToJson string) *BWGraph, error {
    var fioJSON interface{}

    data, err := os.ReadFile(pathToJson)
    if err != nil {
        return err
    }

    err := json.Unmarshal(data, &f)

}
