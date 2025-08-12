default_general_settings = r'''
{
    "ResultsDirectory": "",
    "ResultsDirectoryType": "Domain-Date",
    "ImagesDirectory": "",
    "SaveImages": false,
    "Secrets": {
        "MONDAY_TOKEN": "",
        "OAUTH_CLIENT": ""
    }
}
'''

default_domain_settings = r'''{
  "broadcast": {
    "id": "",
    "page": "",
    "name": ""
  },
  "products": {
    "mondayId": 0,
    "partnersFolderId": "",
    "allowedStatuses": [
      "Live"
    ],
    "trackingLink": {
      "type": "",
      "endType": "offer | IMG-IT | IMG-IT-NUM",
      "template": "[TRACKING_ID] [END]"
    },
    "priority": {
      "tableID": "",
      "pages": [
        ""
      ],
      "textColumn": "C",
      "linkColumn": "F",
      "idColumn": "D",
      "unsubLinkTemplate": "[UNSUB_ID]"
    }
  },
  "styles": {
    "antispam": true,
    "addEsButton": false,
    "antispamReplacements": {
      "a": "а"
    },
    "fontSize": "21px",
    "fontFamily": "Tahoma",
    "linksColor": "random-blue | #ffffff",
    "sideElementsPadding": [
      "26px",
      "27px",
      "28px",
      "29px"
    ],
    "upperDownElementsPadding": [
      "11px",
      "12px",
      "13px"
    ],
    "upperDownCopyPadding": "",
    "lineHeight": {
      "min": 1.5001,
      "max": 1.5099
    },
    "priorityBlock": "[PRIORITY_BODY]<br><br>",
    "priorityBlockLink": "<b><a target=\"_blank\" href=\"[PRIORITY_UNSUB_URL]\" style=\"text-decoration: underline; color: #ffffff;\">[PRIORITY_UNSUB_TEXT_URL]</a></b>",
    "imageBlock": "<table align=\"center\"><tr>\n  <td height=\"20\" width=\"100%\" style=\"max-width: 100%\" class=\"horizontal-space\"></td>\n</tr>\n<tr>\n  <td class=\"img-bg-block\" align=\"center\">\n    <a href=\"urlhere\" target=\"_blank\">\n      <img alt=\"ALT_TEXT\" height=\"auto\" src=\"IMAGE_URL\" style=\"border:0;display:block;outline:none;text-decoration:none;height:auto;width:100%;width: 550px;font-size:13px;\" width=\"280\" />\n        </a>\n  </td>\n</tr>\n<tr>\n  <td height=\"20\" width=\"100%\" style=\"max-width: 100%\" class=\"horizontal-space\"></td>\n</tr></table>"
  }
}'''

default_domain_template = r'''
<!--COPY_STARTS_HERE-->
<!--COPY_STARTS_HERE-->
<!--COPY_STARTS_HERE-->
<!--COPY_STARTS_HERE-->


[COPY_HERE]


<!--COPY_END_HERE-->
<!--COPY_END_HERE-->
<!--COPY_END_HERE-->
<!--COPY_END_HERE-->


<br><br><br>


<!--FOOTER_START_HERE-->
<!--FOOTER_START_HERE-->
<!--FOOTER_START_HERE-->
<!--FOOTER_START_HERE-->


[PRIORITY_FOOTER_HERE]


<!--FOOTER_END_HERE-->
<!--FOOTER_END_HERE-->
<!--FOOTER_END_HERE-->
<!--FOOTER_END_HERE-->
'''
