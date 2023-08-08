package graph

import (
    "os"

    "encoding/json"
)

const (
    BWGraphName string = "Bandwidth"
    BWXLabel string = "Env + Storage IO Engine"
    BWYLabel string = "KiB/s"
    JsonJobsKey string = "jobs"
    JsonReadKey string = "read"
    JsonWriteKey string = "write"
    JsonBWKey string = "bw_avg"
)

func LoadBWGraph(pathToJson string) [string], error {
    var fioJSON interface{}

    data, err := os.ReadFile(pathToJson)
    if err != nil {
        return err
    }

    err := json.Unmarshal(data, &f)

    // TODO: read bw_avg as y-axis
    // TODO: dynamically determine x-axis label from jobname
    // TODO: determine from job-name if read or write
    // TODO: create read and write plots
    // TODO: dynamically determine y-axis tick-size from max bw_avg

}
