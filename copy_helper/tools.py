import json
import logging

import requests


def read_json_file(path):
    logging.debug(f'Reading json file {path}')
    with open(path, 'r', encoding="utf-8") as file:
        return json.load(file)


def write_json_file(path, data):
    logging.debug(f'Writing to {path}')
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)


def get_product_info_from_monday(token, board_id, product_name):
    query = """
    query ($boardId: ID!, $value: CompareValue!) {
      boards(ids: [$boardId]) {
        items_page(query_params: {rules: [{column_id: "name", compare_value: $value, operator: contains_text}]}) {
          items {
            id
            name
            column_values {
              id
              text
            }
          }
        }
      }
    }
    """

    variables = {
        "boardId": board_id,
        "value": product_name,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        'https://api.monday.com/v2',
        json={"query": query, "variables": variables},
        headers=headers
    )

    raw_response_dict = response.json()

    return raw_response_dict['data']['boards'][0]['items_page']['items'][0]
