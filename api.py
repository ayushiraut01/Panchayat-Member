from flask import Flask, jsonify, request, render_template
import pandas as pd
from typing import Dict, List
import json

app = Flask(__name__)

# Global DataFrame
df = None

# Load and prepare data
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(
            "panchayat_data_with_members.csv",
            on_bad_lines="skip",
            header=0
        )
        df.columns = [
            "state_code",
            "state",
            "district_code",
            "district",
            "taluk_code",
            "taluk",
            "village_code",
            "village",
            "member_id",
            "name",
            "phone",
            "email",
            "role",
        ]
        code_columns = ["state_code", "district_code", "taluk_code", "village_code"]
        for col in code_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=code_columns)
        for col in code_columns:
            df[col] = df[col].astype(int)
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame(
            columns=[
                "state_code",
                "state",
                "district_code",
                "district",
                "taluk_code",
                "taluk",
                "village_code",
                "village",
                "member_id",
                "name",
                "phone",
                "email",
                "role",
            ]
        )

df = load_data()

# Main route to serve the HTML
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/states", methods=["GET"])
def get_states():
    states = df[["state_code", "state"]].drop_duplicates().to_dict("records")
    return jsonify(states)

@app.route("/api/districts/<state_code>", methods=["GET"])
def get_districts(state_code):
    try:
        state_code = int(state_code)
        districts = (
            df[df["state_code"] == state_code][["district_code", "district"]]
            .drop_duplicates()
            .to_dict("records")
        )
        return jsonify(districts)
    except:
        return jsonify([])

@app.route("/api/taluks/<district_code>", methods=["GET"])
def get_taluks(district_code):
    try:
        district_code = int(district_code)
        taluks = (
            df[df["district_code"] == district_code][["taluk_code", "taluk"]]
            .drop_duplicates()
            .to_dict("records")
        )
        return jsonify(taluks)
    except:
        return jsonify([])

@app.route("/api/villages/<taluk_code>", methods=["GET"])
def get_villages(taluk_code):
    try:
        taluk_code = int(taluk_code)
        villages = (
            df[df["taluk_code"] == taluk_code][["village_code", "village"]]
            .drop_duplicates()
            .to_dict("records")
        )
        return jsonify(villages)
    except:
        return jsonify([])

@app.route("/api/members", methods=["GET"])
def get_members():
    try:
        filters = {}
        if request.args.get("village_code"):
            filters["village_code"] = int(request.args.get("village_code"))
        filtered_df = df
        for key, value in filters.items():
            filtered_df = filtered_df[filtered_df[key] == value]
        members = filtered_df[
            [
                "name",
                "role",
                "phone",
                "email",
                "village",
                "taluk",
                "district",
                "state",
            ]
        ].to_dict("records")
        return jsonify(members)
    except Exception as e:
        print(f"Error in get_members: {str(e)}")
        return jsonify([])

@app.route("/api/members/add", methods=["POST"])
def add_member():
    global df
    try:
        data = request.json
        village_data = df[df["village_code"] == int(data["village_code"])].iloc[0]
        new_member = {
            "state_code": village_data["state_code"],
            "state": village_data["state"],
            "district_code": village_data["district_code"],
            "district": village_data["district"],
            "taluk_code": village_data["taluk_code"],
            "taluk": village_data["taluk"],
            "village_code": int(data["village_code"]),
            "village": village_data["village"],
            "member_id": df["member_id"].max() + 1,
            "name": data["name"],
            "phone": data["phone"],
            "email": data["email"],
            "role": data["role"],
        }
        df = pd.concat([df, pd.DataFrame([new_member])], ignore_index=True)
        df.to_csv("panchayat_data_with_members.csv", index=False)
        return jsonify({"success": True, "message": "Member added successfully"})
    except Exception as e:
        print(f"Error adding member: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400

# Updated global search route to handle state/district/taluk/village
@app.route("/api/search")
def search():
    search_term = request.args.get("term", "").lower()
    if not search_term or len(search_term) < 2:
        return jsonify({"results": []})

    try:
        # Use the global df (already loaded) instead of reading CSV again
        mask = (
            df["state"].str.lower().str.contains(search_term, na=False)
            | df["district"].str.lower().str.contains(search_term, na=False)
            | df["taluk"].str.lower().str.contains(search_term, na=False)
            | df["village"].str.lower().str.contains(search_term, na=False)
        )
        results = (
            df[mask][
                [
                    "state_code",
                    "state",
                    "district_code",
                    "district",
                    "taluk_code",
                    "taluk",
                    "village_code",
                    "village",
                ]
            ]
            .drop_duplicates()
            .head(10)
        )
        results_list = []
        for _, row in results.iterrows():
            results_list.append(
                {
                    "state_code": row["state_code"],
                    "state": row["state"],
                    "district_code": row["district_code"],
                    "district": row["district"],
                    "taluk_code": row["taluk_code"],
                    "taluk": row["taluk"],
                    "village_code": row["village_code"],
                    "village": row["village"],
                }
            )
        return jsonify({"results": results_list})
    except Exception as e:
        print(f"Error in search: {str(e)}")
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    print(f"Total records loaded: {len(df)}")
    print(f"Unique states: {df['state'].nunique()}")
    print(f"Unique districts: {df['district'].nunique()}")
    print("Sample data:")
    print(df.head())
    app.run(host="0.0.0.0", port=port, debug=True)