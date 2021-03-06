"""
openapi: 3.0.1
info:
  title: Python Cookbook Chapter 12, recipe 3.
  version: "1.0"
servers:
- url: "http://127.0.0.1:5000/dealer"
paths:
  /hands:
    get:
      parameters:
      - name: cards
        in: query
        style: form
        explode: true
        schema:
          type: integer
      responses:
        200:
          description: one hand of cards for each `hand` value in the query string
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    hand:
                      type: integer
                    cards:
                      type: array
                      items:
                        $ref: "#/components/schemas/Card"
  /hand:
    get:
      parameters:
      - name: cards
        in: query
        content:
          application/json:
            schema:
              type: string
              default: "5"
      responses:
        200:
          description: One hand of cards with a size given by the hand value in
            the query string
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Card"
components:
  schemas:
    Card:
      type: object
      properties:
        __class__:
          type: string
          example: "Card"
        rank:
          type: integer
          example: 1
        suit:
          type: string
          example: "\u2660"
"""
import random
from http import HTTPStatus
import os
from typing import Optional

from flask import Flask, jsonify, request, abort, Response
import yaml
from Chapter_12.ch12_r01 import Card, Deck

dealer = Flask("dealer")
dealer.DEBUG = True
dealer.TESTING = True

specification = yaml.load(__doc__, Loader=yaml.SafeLoader)

deck: Optional[Deck] = None


def get_deck() -> Deck:
    global deck
    if deck is None:
        random.seed(os.environ.get("DEAL_APP_SEED"))
        deck = Deck()
    return deck


@dealer.before_request
def check_json() -> Optional[Response]:
    # Special case for these paths only.
    # It is RECOMMENDED that the root OpenAPI document be named: openapi.json or openapi.yaml.
    if request.path in ("/dealer/openapi.yaml", "/dealer/openapi.json"):
        return None
    if "json" in request.headers.get("Accept", "*/*"):
        return None
    if "json" == request.args.get("$format", "html"):
        return None
    return abort(HTTPStatus.BAD_REQUEST)


from flask import send_file

# @dealer.route('/dealer/openapi.yaml')
def swagger1() -> Response:
    # Note. No IANA registered standard as of this writing.
    response = send_file("openapi.yaml", mimetype="application/yaml")
    return response


from flask import make_response


@dealer.route("/dealer/openapi.yaml")
def swagger2() -> Response:
    response = make_response(yaml.dump(specification).encode("utf-8"))
    # Note. No IANA registered standard as of this writing.
    response.headers["Content-Type"] = "application/yaml"
    return response


from flask import make_response
import json


@dealer.route("/dealer/openapi.json")
def swagger3() -> Response:
    response = make_response(json.dumps(specification, indent=2).encode("utf-8"))
    response.headers["Content-Type"] = "application/json"
    return response


@dealer.route("/dealer/hand")
def deal() -> Response:
    try:
        hand_size = int(request.args.get("cards", 5))
        assert 1 <= hand_size < 53
    except Exception as ex:
        abort(HTTPStatus.BAD_REQUEST)
    deck = get_deck()
    cards = deck.deal(hand_size)
    response = jsonify([card.to_json() for card in cards])
    return response


@dealer.route("/dealer/hands")
def multi_hand() -> Response:
    try:
        dealer.logger.info(f"Request: {request.args}")
        hand_sizes = request.args.getlist("cards", type=int)
        dealer.logger.info(f"{hand_sizes=}")
        if len(hand_sizes) == 0:
            hand_sizes = [13, 13, 13, 13]
        assert all(1 <= hand_size < 53 for hand_size in hand_sizes)
        assert sum(hand_sizes) < 53
    except (AssertionError, ValueError) as ex:
        dealer.logger.exception(ex)
        abort(HTTPStatus.BAD_REQUEST)
    deck = get_deck()
    hands = [deck.deal(hand_size) for hand_size in hand_sizes]
    response = jsonify(
        [
            {"hand": i, "cards": [card.to_json() for card in hand]}
            for i, hand in enumerate(hands)
        ]
    )
    return response


if __name__ == "__main__":
    dealer.run(use_reloader=True, threaded=False)
"""
Start with this to force a particular seed to get a consistent result.
::

    DEAL_APP_SEED=42 PYTHONPATH=. python chapter_12/ch12_r03.py

Get the OpenAPI spec
::

    curl http://127.0.0.1:5000/dealer/openapi.yaml --header accept:application/json

Get a hard of cards
::
    
    % curl 'http://127.0.0.1:5000/dealer/hand?cards=5' --header accept:application/json
    [
      {
        "__class__": "Card", 
        "rank": 10, 
        "suit": "\u2661"
      }, 
      {
        "__class__": "Card", 
        "rank": 4, 
        "suit": "\u2661"
      }, 
      {
        "__class__": "Card", 
        "rank": 7, 
        "suit": "\u2660"
      }, 
      {
        "__class__": "Card", 
        "rank": 11, 
        "suit": "\u2662"
      }, 
      {
        "__class__": "Card", 
        "rank": 12, 
        "suit": "\u2661"
      }
    ]

Get multiple hands
::

    % curl 'http://127.0.0.1:5000/dealer/hands?cards=2&cards=1&cards=1&cards=1' --header accept:application/json

    [
      {
        "cards": [
          {
            "__class__": "Card", 
            "rank": 3, 
            "suit": "\u2663"
          }, 
          {
            "__class__": "Card", 
            "rank": 10, 
            "suit": "\u2660"
          }
        ], 
        "hand": 0
      }, 
      {
        "cards": [
          {
            "__class__": "Card", 
            "rank": 9, 
            "suit": "\u2660"
          }
        ], 
        "hand": 1
      }, 
      {
        "cards": [
          {
            "__class__": "Card", 
            "rank": 13, 
            "suit": "\u2663"
          }
        ], 
        "hand": 2
      }, 
      {
        "cards": [
          {
            "__class__": "Card", 
            "rank": 5, 
            "suit": "\u2663"
          }
        ], 
        "hand": 3
      }
    ]
"""
