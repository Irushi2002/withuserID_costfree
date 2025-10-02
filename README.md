###"HOW TO RUN BOTH FRONTEND AND BACKEND"

cd frontend2
npm install
npm start



cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
