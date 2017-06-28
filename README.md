# translation-real-time-validaton [![Build Status](https://travis-ci.org/KeepSafe/translation-real-time-validaton.svg?branch=master)](https://travis-ci.org/KeepSafe/translation-real-time-validaton)

Real time content validation for [WebTranslateIt](https://webtranslateit.com)

**Alpha version** This package is still in development. Though the functionality may work the API and any behavior might change.

## Requirements

* Python 3.5.+

## Installation

`python3 ./setup.py install`

## Usage

This package is a server which should run on a publicly accessible endpoint. It will receive status changes from WebTranslateIt and validate the content and send an email with a diff the the person who's committed the change (if the validation fails).

### Entpoints

#### /translations
	
`POST`

Accepts requests from [WebTranslateIt Web Hook](https://webtranslateit.com/en/docs/webhooks/)

*Right now it only validates markdown.*

#### /projects/{api_key}

`POST {"email"="test@test.com"}`

Validates the entire project. Needs project's private API key. Will send a single email with all errors.

#### /healthcheck

Return 200 if the service is available.


