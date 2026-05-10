from flask import Flask, request, jsonify
from src.pipelines.anomaly_detection_pipeline import run_pipeline
from src.analysis.matplotlib_visualizer import plot_results
from src.analysis.mpf_visualizer import plot_ohlcv
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__) #start a web server on app.py


@app.route("/api/analyze", methods=['POST'])
def analyze():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid or missing body"}), 400


    required_fields = [
        "stock_name", "mode", "dates",
        "timeframe", "features", "models"
    ]


    features = ["close", "volume", "returns", "volatility"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "missing": missing
        }), 400

    # validate date structure
    if "train" not in data["dates"] or "test" not in data["dates"]:
        return jsonify({"error": "train and test must exist inside dates"}), 400

    #extract data 
    stock_name = data["stock_name"]
    mode = data["mode"]
    dates = data["dates"]

    start_date = validate_date(dates["train"]["start"])
    end_date = validate_date(dates["train"]["end"])
    

    timeframe = data["timeframe"]
    features = data["features"]
    models = data["models"]

    top_n = 20

    #Validate date inputs
    valid_date, error_response = handle_date_inputs(
        train_start_date,
        train_end_date,
        test_start_date,
        test_end_date
    )

    if not valid_date:
        return jsonify(error_response), 400

    
    #handle invalid or falsy list

    valid_list,error_response = validate_list(features,"features")
    if not valid_list:
        return jsonify(error_response),400
    
    valid_list,error_response = validate_list(models,"models")
    if not valid_list:
        return jsonify(error_response),400

    isolation_forest_params = {}
    dbscan_params = {}
    z_score_params = {}

    if "isolation_forest" in models:
        default_if_params = {"n_estimators": 200, "contamination": 0.05}
        isolation_forest_params = {
            **default_if_params,
            **data.get("isolation_forest_params", {})
        }

    if "dbscan" in models:
        default_db_params = {
            "eps_list": [0.3, 0.5, 0.7],
            "min_pts_list": [3, 5, 10]
        }
        dbscan_params = {
            **default_db_params,
            **data.get("dbscan_params", {})
        }

    if "z_score" in models:
        default_zs_params = {"confidence_level": 0.95}
        z_score_params = {
            **default_zs_params,
            **data.get("z_score_params", {})
        }
    
    dates = {
        "train_start":train_start_date,
        "train_end":train_end_date,
        "test_start":test_start_date,
        "test_end":test_end_date
    }
    params = isolation_forest_params,dbscan_params,z_score_params



    X,df = run_pipeline(
        stock_name,
        dates,
        mode,
        features,
        timeframe
    )


    results,(df_train,df_test) = orchestrate(X,df,models,params);


    response = {}   

    response["ohlcv_img"] = plot_ohlcv(stock_name,df_test,period="Test")

    response["plots"] = {}

    response["anomalies"] = {}

    response['thresholds'] = {}



    for model in models :

        threshold = results[model]["threshold"]

        
        response["plots"][model] = plot_results(mode,stock_name,threshold,df_test,period="Test",model=model)


        top_anoms = df_test.sort_values(f"anomaly_score_{model}", ascending=False).head(top_n).reset_index();

        response["anomalies"][model] = top_anoms[["transaction_time","close","quantity","return",f"anomaly_score_{model}",f"anomalous_{model}"]].to_dict(orient="records")
        
        response["thresholds"][model] = threshold



    return jsonify(response), 200



def validate_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    

def handle_date_inputs(train_start, train_end, test_start, test_end):

    if not all([train_start, train_end, test_start, test_end]):
        return False, {"error": "Invalid date format. Use YYYY-MM-DD"}

    if train_start >= train_end:
        return False, {"error": "train_start must be before train_end"}

    if test_start >= test_end:
        return False, {"error": "test_start must be before test_end"}

    if train_end >= test_start:
        return False, {"error": "train period must be before test period"}

    return True, None


def validate_list(data,list_name):
    if not isinstance(data, list) or not data:
        return False,{"error": f"{list_name} must be a non-empty list"}

    return True,None

if(__name__=='__main__'):
    app.run(debug=True)