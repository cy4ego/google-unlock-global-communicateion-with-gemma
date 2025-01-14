# Goal
See my [kaggle notebook](https://www.kaggle.com/code/cy4ego/fine-tune-gemma2-to-revive-joseon-s-korea-legacy)
# How to
## Prepare environments
```
conda create -n gemma2 python=3.10
conda activate gemma2
python -m pip install -r ./requirements.txt
```

## How to download data
```
python ./download_data.py
```

## How to fine-tune gemma2
Run gemma2_fine_tune_keras.ipynb

# Dataset
## Crawling
- Collect the raw data using selenium from the [朝鮮王朝實錄-조선왕조실록(The Veritable Records of the Josen Dynasty)](https://sillok.history.go.kr/) - 1392.07.17 ~ 1928.07.06
- Run the following code in a local environment
  - It downloads the Veritable Records of 25 kings(Silok), which means it does not include the records of `Gojong` and `Sunjong`. The total size of the downloaded files is about 1GB.
  - `in_local`: Set this to `False` in a kaggle environment. Avoid running this code in Kaggle to download the data, as it may take more than a week.
  - `debug`: Set this to `True` when running the code on a local PC for testing. This will download onley the partial records of the first king. Otherwise, set it to `False`, meaning it will download the records from `Taejo` to `Cheoljong`.
  - `use_multiprocessing`: Set this to `True` if you want run the program using multiprocessing; otherwise set this to False, which is more stable.
  - `random_sleep`: Without it, you will encouter an `HttpConnectionPool Read timed out error`.
- data format(jsonl): list of dict(json)
  ```
  [
      {'title': "title_of_the_text", 'hanja': "朝鮮王朝實錄", 'hangul': "조선왕조실록", 'url': "https://sillok.history.go.kr/"},
      {'title': ... },
  ]
  ```
  - `title`: When the text was written
  - `hanja`: Korean Chinese Text
  - `hangul`: Modern Korean
  - `url`: Where to find the text 
- Coverage
  - Duration: `Taejo` ~ `Cheoljong`(태조 ~ 철종(1392년 ~ 1863년))
  - Total data size: about 1 GB(~1000 MB)
  - Total number of files: 25 files