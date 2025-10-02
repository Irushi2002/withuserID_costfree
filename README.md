###"HOW TO RUN BOTH FRONTEND AND BACKEND"

cd frontend2

npm install

npm start


//BACKEND RUN

cd backend

pip install -r requirements.txt

python -m uvicorn main:app --reload
