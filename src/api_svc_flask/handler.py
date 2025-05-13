#!/usr/bin/env python3

import boto3
import requests
import json
import logging
import os
import hmac
import datetime
from urllib.parse import urlparse

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify(status=200, message='Hello Flask!')

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({"users": ["123", "456"]})

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify({"user_id": user_id, "name": f"User {user_id}"})

# Error handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify(error=str(e)), 500

# AWS Lambda handler
def main(event, context):
    # API Gateway HTTP API integration
    path = event.get("path", "")
    http_method = event.get("httpMethod", "")
    headers = event.get("headers", {})
    query_params = event.get("queryStringParameters", {}) or {}
    path_params = event.get("pathParameters", {}) or {}
    body = event.get("body", "")
    
    # Create a Flask request context
    with app.test_request_context(
        path=path,
        method=http_method,
        headers=headers,
        query_string=query_params,
        data=body,
    ):
        # Add path parameters to the request
        request.path_params = path_params
        
        try:
            # Process the request and get the response
            response = app.full_dispatch_request()
            return {
                "statusCode": response.status_code,
                "body": response.get_data(as_text=True),
                "headers": dict(response.headers),
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": str(e),
                "headers": {"Content-Type": "application/json"},
            }