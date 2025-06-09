
# Prompt Engineering Tool

> **A script for extracting fatigue specimen information from literature using a Large Language Model API**  
> `prompt engineering.py`

---

## 📌 Main Features

| Module | Description |
|--------|-------------|
| **prompt engineering.py** | Batch processing of `.docx` / `.txt` files, calling a Large Language Model to extract fatigue specimen parameters and S‑N / e‑N data. Results are saved as plain text. |

| Parameters |
|-----------|
| `Title` |
| `Base Material` |
| `Base Young's Modulus (GPa)` |
| `Base Yield Strength (MPa)` |
| `Base Ultimate Tensile Strength (MPa)` |
| `Base Elongation (%)` |
| `Weld Material` |
| `Weld Young's Modulus (GPa)` |
| `Weld Yield Strength (MPa)` |
| `Weld Ultimate Tensile Strength (MPa)` |
| `Weld Elongation (%)` |
| `Processing` |
| `Type of welding joint` |
| `Welding method` |
| `Welding voltage (V)` |
| `Welding current (A)` |
| `Welding speed (mm/s)` |
| `Preheat temperature of Welding (°C)` |
| `Welding environment` |
| `Residual Stress` |
| `Type of fatigue specimen` |
| `Thickness (mm) of fatigue specimen` |
| `Types of fatigue tests` |
| `Fatigue test temperature (°C)` |
| `Fatigue test environment` |
| `Load ratio of fatigue test` |
| `Frequency (Hz) of fatigue test` |
| `Fatigue test machine` |
| `Fatigue test standard` |
| `Fatigue test control` |
| `Stress concentration factor` |
| `Failure location` |

---

## 🗂️ Directory Structure

```
project/
├── prompt engineering.py      # Main execution script
├── .env                       # Stores Large Language Model API key
└── README.md                  # This document
```

---

## ⚙️ Installation & Configuration

1. **Install dependencies**
   ```bash
   openai>=1.0.0          
   python-dotenv>=1.0.0   
   python-docx>=0.8.11    
   ```

2. **Set environment variables**  
   Create a `.env` file in the project root directory with the following content:
   ```ini
   DEEPSEEK_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🚀 Usage

```bash
python prompt engineering.py     --input "F:/unprocessed"     --output "F:/processed"
```

Script workflow:

1. Recursively scan `.docx` / `.txt` files in the `--input` directory  
2. Call the Large Language Model API to extract fields according to prompts  
3. Write the result of each document into a corresponding `.txt` and generate `process.log` to track success/failure

---

## 📄 Output Example

```
└─processed
   ├── sample1.txt   # Extraction result
   ├── sample2.txt
   └── process.log   # Run log
```

---

## 📝 Customization

To add or modify extracted fields, edit the `SYSTEM_MESSAGE_CONTENT` variable in `prompt engineering.py`, then rerun the script.  
You can also switch to a different Large Language Model as needed.

---

## ❓ FAQ

| Issue | Solution |
|-------|----------|
| **RateLimitError** | The LLM API is rate-limited. Exponential backoff is implemented; reduce QPS if errors persist. |
| **Unsupported file type** | Only `.docx` / `.txt` are supported. Please convert other formats first. |
| **Encoding issue** | Defaults to `utf‑8`. Check the source file if garbled text appears. |
