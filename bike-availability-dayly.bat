@echo off
CALL "C:\Users\isakn\miniconda3\condabin\conda.bat" activate SML_Project

jupyter nbconvert --execute --to notebook --inplace "C:\GitHub\ID2223-Project\3_git_to_hopsworks_daily_pipeline.ipynb"
jupyter nbconvert --execute --to notebook --inplace "C:\GitHub\ID2223-Project\5_inference.ipynb"

cd C:\GitHub\ID2223-Project

git add .
git commit -m "Update daily pipeline"
git push