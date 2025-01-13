from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    percentile = "99th"
    timeframe = "1 Day"

    regions = [
        {"region_name": "Lorem ipsum 1", "region": "af-south-1"},
        {"region_name": "Lorem ipsum 2", "region": "ap-east-1"},
        {"region_name": "Lorem ipsum 3", "region": "ap-northeast-1"},
        {"region_name": "Lorem ipsum 4", "region": "ap-northeast-2"},
        {"region_name": "Lorem ipsum 5", "region": "ap-northeast-3"},
        {"region_name": "Lorem ipsum 6", "region": "ap-south-1"},
        {"region_name": "Lorem ipsum 7", "region": "ap-southeast-1"},
        {"region_name": "Lorem ipsum 8", "region": "ap-southeast-2"},
        {"region_name": "Lorem ipsum 9", "region": "ca-central-1"},
        {"region_name": "Lorem ipsum 10", "region": "eu-central-1"},
        {"region_name": "Lorem ipsum 11", "region": "eu-north-1"},
        {"region_name": "Lorem ipsum 12", "region": "eu-south-1"},
        {"region_name": "Lorem ipsum 13", "region": "eu-west-1"},
        {"region_name": "Lorem ipsum 14", "region": "eu-west-2"},
        {"region_name": "Lorem ipsum 15", "region": "eu-west-3"},
        {"region_name": "Lorem ipsum 16", "region": "me-south-1"},
        {"region_name": "Lorem ipsum 17", "region": "sa-east-1"},
        {"region_name": "Lorem ipsum 18", "region": "us-east-1"},
        {"region_name": "Lorem ipsum 19", "region": "us-east-2"},
        {"region_name": "Lorem ipsum 20", "region": "us-west-1"},
        {"region_name": "Lorem ipsum 21", "region": "us-west-2"}
    ]

    values = {
        "af-south-1": {
            "af-south-1": {"ping": 8.58},
            "ap-east-1": {"ping": 374.11},
            "ap-northeast-1": {"ping": 355.68},
            "ap-northeast-2": {"ping": 408.21},
            "ap-northeast-3": {"ping": 384.56},
            "ap-south-1": {"ping": 283.39},
            "ap-southeast-1": {"ping": 347.11},
            "ap-southeast-2": {"ping": 408.76},
            "ca-central-1": {"ping": 221.97},
            "eu-central-1": {"ping": 154.14},
            "eu-north-1": {"ping": 175.09},
            "eu-south-1": {"ping": 194.31},
            "eu-west-1": {"ping": 158.85},
            "eu-west-2": {"ping": 148.89},
            "eu-west-3": {"ping": 143.1},
            "me-south-1": {"ping": 251.77},
            "sa-east-1": {"ping": 336.71},
            "us-east-1": {"ping": 226.95},
            "us-east-2": {"ping": 235.66},
            "us-west-1": {"ping": 288.16},
            "us-west-2": {"ping": 273.67}
        },
        "ap-east-1": {
            "af-south-1": {"ping": 381.21},
            "ap-east-1": {"ping": 2.89},
            "ap-northeast-1": {"ping": 52.43},
            "ap-northeast-2": {"ping": 39.52},
            "ap-northeast-3": {"ping": 47.01},
            "ap-south-1": {"ping": 96.73},
            "ap-southeast-1": {"ping": 34.92},
            "ap-southeast-2": {"ping": 126.8},
            "ca-central-1": {"ping": 192.63},
            "eu-central-1": {"ping": 193.8},
            "eu-north-1": {"ping": 213.99},
            "eu-south-1": {"ping": 186.14},
            "eu-west-1": {"ping": 227.69},
            "eu-west-2": {"ping": 210.02},
            "eu-west-3": {"ping": 202.82},
            "me-south-1": {"ping": 128.29},
            "sa-east-1": {"ping": 306.35},
            "us-east-1": {"ping": 196.3},
            "us-east-2": {"ping": 182.14},
            "us-west-1": {"ping": 153.61},
            "us-west-2": {"ping": 144.94}
        },
        "ap-northeast-1": {
            "af-south-1": {"ping": 359.17},
            "ap-east-1": {"ping": 51.17},
            "ap-northeast-1": {"ping": 3.16},
            "ap-northeast-2": {"ping": 37.37},
            "ap-northeast-3": {"ping": 9.99},
            "ap-south-1": {"ping": 145.55},
            "ap-southeast-1": {"ping": 70.71},
            "ap-southeast-2": {"ping": 109.56},
            "ca-central-1": {"ping": 144.8},
            "eu-central-1": {"ping": 227.99},
            "eu-north-1": {"ping": 249.1},
            "eu-south-1": {"ping": 218.24},
            "eu-west-1": {"ping": 200.49},
            "eu-west-2": {"ping": 211.13},
            "eu-west-3": {"ping": 217.38},
            "me-south-1": {"ping": 177.17},
            "sa-east-1": {"ping": 256.39},
            "us-east-1": {"ping": 145.81},
            "us-east-2": {"ping": 133.11},
            "us-west-1": {"ping": 109.02},
            "us-west-2": {"ping": 98.87}
        },
        "ap-northeast-2": {
            "af-south-1": {"ping": 410.61},
            "ap-east-1": {"ping": 39.98},
            "ap-northeast-1": {"ping": 35.48},
            "ap-northeast-2": {"ping": 5.22},
            "ap-northeast-3": {"ping": 25.31},
            "ap-south-1": {"ping": 137.81},
            "ap-southeast-1": {"ping": 74.73},
            "ap-southeast-2": {"ping": 144.76},
            "ca-central-1": {"ping": 174.41},
            "eu-central-1": {"ping": 231.41},
            "eu-north-1": {"ping": 250.38},
            "eu-south-1": {"ping": 221.89},
            "eu-west-1": {"ping": 229.48},
            "eu-west-2": {"ping": 242.52},
            "eu-west-3": {"ping": 246.28},
            "me-south-1": {"ping": 164.07},
            "sa-east-1": {"ping": 288.09},
            "us-east-1": {"ping": 175.82},
            "us-east-2": {"ping": 162.16},
            "us-west-1": {"ping": 133.85},
            "us-west-2": {"ping": 124.59}
        },
        "ap-northeast-3": {
            "af-south-1": {"ping": 390.18},
            "ap-east-1": {"ping": 45.37},
            "ap-northeast-1": {"ping": 9.95},
            "ap-northeast-2": {"ping": 25.53},
            "ap-northeast-3": {"ping": 2.31},
            "ap-south-1": {"ping": 137.35},
            "ap-southeast-1": {"ping": 75.17},
            "ap-southeast-2": {"ping": 121.45},
            "ca-central-1": {"ping": 150.05},
            "eu-central-1": {"ping": 232.81},
            "eu-north-1": {"ping": 252.3},
            "eu-south-1": {"ping": 223.72},
            "eu-west-1": {"ping": 206.31},
            "eu-west-2": {"ping": 216.55},
            "eu-west-3": {"ping": 223.48},
            "me-south-1": {"ping": 169.75},
            "sa-east-1": {"ping": 262.35},
            "us-east-1": {"ping": 153.12},
            "us-east-2": {"ping": 139.31},
            "us-west-1": {"ping": 109.87},
            "us-west-2": {"ping": 100.02}
        },
        "ap-south-1": {
            "af-south-1": {"ping": 289.81},
            "ap-east-1": {"ping": 96.64},
            "ap-northeast-1": {"ping": 143.34},
            "ap-northeast-2": {"ping": 135.36},
            "ap-northeast-3": {"ping": 136.05},
            "ap-south-1": {"ping": 2.36},
            "ap-southeast-1": {"ping": 64.18},
            "ap-southeast-2": {"ping": 155.44},
            "ca-central-1": {"ping": 189.23},
            "eu-central-1": {"ping": 127.87},
            "eu-north-1": {"ping": 148.39},
            "eu-south-1": {"ping": 112.14},
            "eu-west-1": {"ping": 125.98},
            "eu-west-2": {"ping": 115.36},
            "eu-west-3": {"ping": 107.33},
            "me-south-1": {"ping": 37.17},
            "sa-east-1": {"ping": 299.33},
            "us-east-1": {"ping": 187.95},
            "us-east-2": {"ping": 198.55},
            "us-west-1": {"ping": 239.53},
            "us-west-2": {"ping": 231.07}
        },
        "ap-southeast-1": {
            "af-south-1": {"ping": 346.82},
            "ap-east-1": {"ping": 35.22},
            "ap-northeast-1": {"ping": 72.32},
            "ap-northeast-2": {"ping": 75.09},
            "ap-northeast-3": {"ping": 75.61},
            "ap-south-1": {"ping": 65.92},
            "ap-southeast-1": {"ping": 4.14},
            "ap-southeast-2": {"ping": 94.28},
            "ca-central-1": {"ping": 215.12},
            "eu-central-1": {"ping": 160.55},
            "eu-north-1": {"ping": 183.0},
            "eu-south-1": {"ping": 153.03},
            "eu-west-1": {"ping": 185.74},
            "eu-west-2": {"ping": 177.54},
            "eu-west-3": {"ping": 171.27},
            "me-south-1": {"ping": 98.94},
            "sa-east-1": {"ping": 327.84},
            "us-east-1": {"ping": 217.76},
            "us-east-2": {"ping": 205.11},
            "us-west-1": {"ping": 174.73},
            "us-west-2": {"ping": 164.5}
        },
        "ap-southeast-2": {
            "af-south-1": {"ping": 413.5},
            "ap-east-1": {"ping": 126.13},
            "ap-northeast-1": {"ping": 106.06},
            "ap-northeast-2": {"ping": 148.84},
            "ap-northeast-3": {"ping": 121.04},
            "ap-south-1": {"ping": 154.21},
            "ap-southeast-1": {"ping": 94.19},
            "ap-southeast-2": {"ping": 5.02},
            "ca-central-1": {"ping": 199.34},
            "eu-central-1": {"ping": 251.37},
            "eu-north-1": {"ping": 271.77},
            "eu-south-1": {"ping": 241.96},
            "eu-west-1": {"ping": 256.92},
            "eu-west-2": {"ping": 265.28},
            "eu-west-3": {"ping": 280.78},
            "me-south-1": {"ping": 190.02},
            "sa-east-1": {"ping": 311.93},
            "us-east-1": {"ping": 199.21},
            "us-east-2": {"ping": 189.21},
            "us-west-1": {"ping": 139.9},
            "us-west-2": {"ping": 140.54}
        },
        "ca-central-1": {
            "af-south-1": {"ping": 226.5},
            "ap-east-1": {"ping": 193.33},
            "ap-northeast-1": {"ping": 143.49},
            "ap-northeast-2": {"ping": 175.47},
            "ap-northeast-3": {"ping": 150.06},
            "ap-south-1": {"ping": 192.54},
            "ap-southeast-1": {"ping": 215.32},
            "ap-southeast-2": {"ping": 201.85},
            "ca-central-1": {"ping": 7.3},
            "eu-central-1": {"ping": 93.82},
            "eu-north-1": {"ping": 105.83},
            "eu-south-1": {"ping": 100.68},
            "eu-west-1": {"ping": 68.79},
            "eu-west-2": {"ping": 82.78},
            "eu-west-3": {"ping": 85.99},
            "me-south-1": {"ping": 162.81},
            "sa-east-1": {"ping": 125.69},
            "us-east-1": {"ping": 16.08},
            "us-east-2": {"ping": 27.04},
            "us-west-1": {"ping": 79.88},
            "us-west-2": {"ping": 60.78}
        },
        "eu-central-1": {
            "af-south-1": {"ping": 154.76},
            "ap-east-1": {"ping": 192.22},
            "ap-northeast-1": {"ping": 227.6},
            "ap-northeast-2": {"ping": 231.6},
            "ap-northeast-3": {"ping": 232.4},
            "ap-south-1": {"ping": 127.82},
            "ap-southeast-1": {"ping": 160.43},
            "ap-southeast-2": {"ping": 250.8},
            "ca-central-1": {"ping": 92.09},
            "eu-central-1": {"ping": 3.97},
            "eu-north-1": {"ping": 23.74},
            "eu-south-1": {"ping": 11.49},
            "eu-west-1": {"ping": 27.13},
            "eu-west-2": {"ping": 18.2},
            "eu-west-3": {"ping": 12.72},
            "me-south-1": {"ping": 84.93},
            "sa-east-1": {"ping": 204.36},
            "us-east-1": {"ping": 92.33},
            "us-east-2": {"ping": 104.44},
            "us-west-1": {"ping": 152.13},
            "us-west-2": {"ping": 141.37}
        }
    }

    # Latency thresholds for coloring
    thresholds = {
        "low": 100,   # < 100ms
        "medium": 180,  # 100ms - 180ms
        "high": float('inf')  # > 180ms
    }

    for region_from in regions:
        for region_to in regions:
            from_region = region_from['region']
            to_region = region_to['region']

            # Ensure keys exist
            if from_region not in values:
                values[from_region] = {}

            if to_region not in values[from_region]:
                values[from_region][to_region] = {"ping": float('inf')}
            else:
                # Ensure ping is a number
                if isinstance(values[from_region][to_region]["ping"], str):
                    values[from_region][to_region]["ping"] = float('inf')

    # Return the rendered HTML
    return render_template(
      "index.html",
      regions_to=regions,
      regions_from=regions,
      values=values,
      show_data="ping"
    )


if __name__ == "__main__":
     app.run(debug=True, host="0.0.0.0", port=5000)