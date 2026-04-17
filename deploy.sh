#!/bin/bash
set -e

FUNCTION_NAME="grocery-whatsapp-bot"
ROLE_NAME="grocery-bot-role"
API_NAME="grocery-bot-api"
REGION="sa-east-1"
RUNTIME="python3.13"

echo "==> 1. Fetching IAM role ARN (create it manually in the Console if missing)..."
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")
if [ -z "$ROLE_ARN" ]; then
  echo ""
  echo "ERROR: Role '$ROLE_NAME' not found."
  echo "Create it manually in the AWS Console:"
  echo "  IAM → Roles → Create role → AWS service → Lambda"
  echo "  Attach: AWSLambdaBasicExecutionRole"
  echo "  Name: $ROLE_NAME"
  exit 1
fi
echo "Role ARN: $ROLE_ARN"

echo "==> 2. Packaging Lambda function..."
rm -rf /tmp/lambda-package && mkdir /tmp/lambda-package
pip install -r requirements.txt -t /tmp/lambda-package --quiet
cp lambda_function.py db.py models.py crud.py parser.py categories.py /tmp/lambda-package/
cd /tmp/lambda-package && zip -r /tmp/function.zip . -q && cd -
echo "Package size: $(du -sh /tmp/function.zip | cut -f1)"

DB_PASSWORD=$(cat .password)

echo "==> 3. Deploying Lambda function..."
# Small sleep to let IAM role propagate
sleep 10

EXISTING=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null || echo "")

if [ -z "$EXISTING" ]; then
  aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --role "$ROLE_ARN" \
    --handler lambda_function.handler \
    --zip-file fileb:///tmp/function.zip \
    --environment "Variables={DB_PASSWORD=$DB_PASSWORD}" \
    --timeout 30 \
    --region "$REGION"
  echo "Lambda created."
else
  aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb:///tmp/function.zip \
    --region "$REGION"
  aws lambda wait function-updated \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION"
  aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --environment "Variables={DB_PASSWORD=$DB_PASSWORD}" \
    --region "$REGION"
  echo "Lambda updated."
fi

LAMBDA_ARN=$(aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'Configuration.FunctionArn' \
  --output text)

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "==> 4. Creating API Gateway..."
EXISTING_API=$(aws apigateway get-rest-apis --region "$REGION" \
  --query "items[?name=='$API_NAME'].id" --output text)

if [ -z "$EXISTING_API" ]; then
  API_ID=$(aws apigateway create-rest-api \
    --name "$API_NAME" \
    --region "$REGION" \
    --query 'id' --output text)
  echo "API created: $API_ID"
else
  API_ID="$EXISTING_API"
  echo "API already exists: $API_ID"
fi

ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id "$API_ID" \
  --region "$REGION" \
  --query 'items[?path==`/`].id' --output text)

RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$API_ID" \
  --region "$REGION" \
  --query 'items[?pathPart==`webhook`].id' --output text)

if [ -z "$RESOURCE_ID" ]; then
  RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$API_ID" \
    --parent-id "$ROOT_ID" \
    --path-part webhook \
    --region "$REGION" \
    --query 'id' --output text)
fi

aws apigateway put-method \
  --rest-api-id "$API_ID" \
  --resource-id "$RESOURCE_ID" \
  --http-method POST \
  --authorization-type NONE \
  --region "$REGION" 2>/dev/null || true

aws apigateway put-integration \
  --rest-api-id "$API_ID" \
  --resource-id "$RESOURCE_ID" \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region "$REGION"

# ---------------------------------------------------------------------------
# /shop  (GET) — shopping web app
# ---------------------------------------------------------------------------
SHOP_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$API_ID" --region "$REGION" \
  --query 'items[?pathPart==`shop`].id' --output text)

if [ -z "$SHOP_RESOURCE_ID" ]; then
  SHOP_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$API_ID" --parent-id "$ROOT_ID" \
    --path-part shop --region "$REGION" --query 'id' --output text)
fi

aws apigateway put-method \
  --rest-api-id "$API_ID" --resource-id "$SHOP_RESOURCE_ID" \
  --http-method GET --authorization-type NONE \
  --region "$REGION" 2>/dev/null || true

aws apigateway put-integration \
  --rest-api-id "$API_ID" --resource-id "$SHOP_RESOURCE_ID" \
  --http-method GET --type AWS_PROXY --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region "$REGION"

# ---------------------------------------------------------------------------
# /shop/finish  (POST) — mark items as purchased
# ---------------------------------------------------------------------------
FINISH_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$API_ID" --region "$REGION" \
  --query 'items[?pathPart==`finish`].id' --output text)

if [ -z "$FINISH_RESOURCE_ID" ]; then
  FINISH_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$API_ID" --parent-id "$SHOP_RESOURCE_ID" \
    --path-part finish --region "$REGION" --query 'id' --output text)
fi

aws apigateway put-method \
  --rest-api-id "$API_ID" --resource-id "$FINISH_RESOURCE_ID" \
  --http-method POST --authorization-type NONE \
  --region "$REGION" 2>/dev/null || true

aws apigateway put-integration \
  --rest-api-id "$API_ID" --resource-id "$FINISH_RESOURCE_ID" \
  --http-method POST --type AWS_PROXY --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region "$REGION"

# ---------------------------------------------------------------------------
# Deploy & permissions
# ---------------------------------------------------------------------------
aws apigateway create-deployment \
  --rest-api-id "$API_ID" --stage-name prod --region "$REGION"

# Remove stale permission if it exists, then re-add with full wildcard scope
aws lambda remove-permission \
  --function-name "$FUNCTION_NAME" --statement-id apigateway-invoke \
  --region "$REGION" 2>/dev/null || true
aws lambda remove-permission \
  --function-name "$FUNCTION_NAME" --statement-id apigateway-invoke-all \
  --region "$REGION" 2>/dev/null || true
aws lambda add-permission \
  --function-name "$FUNCTION_NAME" --statement-id apigateway-invoke-all \
  --action lambda:InvokeFunction --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
  --region "$REGION"

WEBHOOK_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod/webhook"
SHOP_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod/shop"
echo ""
echo "=========================================="
echo "Deployment complete!"
echo "Webhook URL : $WEBHOOK_URL"
echo "Shop base   : $SHOP_URL"
echo "Paste the Webhook URL into Twilio's sandbox settings."
echo "=========================================="
