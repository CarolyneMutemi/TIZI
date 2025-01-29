# Base URL
BASE_URL="https://cebe-41-139-168-163.ngrok-free.app"

# Test GET /users
echo "Testing GET /users..."
curl -X GET "$BASE_URL/users" -H "Content-Type: application/json"
echo -e "\n"

# Test GET /profile
echo "Testing GET /profile..."
curl -X GET "$BASE_URL/profile" -H "Content-Type: application/json"
echo -e "\n"

# Test POST /data
echo "Testing POST /login..."
curl -X POST "$BASE_URL/login" -H "Content-Type: application/json" -d '{
  "email": "kevinisom@gmail.com"
}'
echo -e "\n"

# Test PUT /data/1
echo "Testing PUT /data/1..."
curl -X PUT "$BASE_URL/data/1" -H "Content-Type: application/json" -d '{"key":"updatedValue"}'
echo -e "\n"

# Test DELETE /data/1
echo "Testing DELETE /data/1..."
curl -X DELETE "$BASE_URL/data/1" -H "Content-Type: application/json"
echo -e "\n"

chmod +x test_api.sh&&./test_api.sh
