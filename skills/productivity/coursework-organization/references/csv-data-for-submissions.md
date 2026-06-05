# CSV Data Format for Academic Chapter Submissions

## Why CSV?

Teachers commonly ask students to "use your own data" for chapter code exercises. The standard format across NLP/course projects is:

```
text,label
评论内容1,正面
评论内容2,负面
```

## Column conventions

| Column | Content | Common values |
|--------|---------|---------------|
| `text` | The text to analyze. Also seen as: `Text`, `content`, `Content`, `sentence`, `Sentence`, `评论` | Any Chinese/English text |
| `label` | The sentiment/class label. Also seen as: `Sentiment`, `label`, `Label` | `正面`/`消极` or `POSITIVE`/`NEGATIVE` or `1`/`0` |
| `Sentiment` | Alternative name for label column in some datasets | `积极`/`消极` or `positive`/`negative` |

## Typical conversion pattern

**Textbook original** (hardcoded in Python):

```python
train_data = [
    ("这个手机太差了。", "消极"),
    ("今天的天气真好。", "积极"),
]
```

**Convert to CSV** (`data/my_data.csv`):

```csv
text,label
这个手机太差了。,消极
今天的天气真好。,积极
```

**Update code** to load from CSV:

```python
import pandas as pd
df = pd.read_csv("../data/my_data.csv")
train_texts = df["text"].tolist()
train_labels = df["label"].tolist()
```

## CSV encoding

- **Always use UTF-8** (with BOM for Windows Excel compatibility: `encoding="utf-8-sig"`)
- `pd.read_csv("file.csv")` defaults to UTF-8
- If opening in Excel shows garbled text, add BOM: `df.to_csv("file.csv", encoding="utf-8-sig", index=False)`

## Data distribution best practices

- **Minimum 20 samples** (10 per class) for a demo submission
- Cover diverse topics (food, delivery, service, products, weather, school life) to show the model generalizes
- Keep sentences short (10-40 chars) for TF-IDF to work well
- Avoid extreme sarcasm or mixed-sentiment texts in training data
