# CLI Toolbox

**CLI Toolbox** is a collection of simple **Python command-line tools** designed to automate common tasks such as file processing and image conversion. Each tool in this repository lives in its own folder and can be launched through the **CLI Toolbox gateway (`main.py`)**.

---

## Features

- Interactive command-line tools
- Cross-platform support (Linux, macOS, Windows)
- Beginner-friendly workflow
- Modular toolbox structure
- Easy to extend with new tools
- Centralized dependency management

---

## Available Tools

| Tool | Description |
|------|-------------|
| Image Converter | Convert images between formats such as JPG, PNG, WEBP, BMP, TIFF, and GIF |

More tools will be added over time.

---

## Repository Structure

```text
cli-toolbox/
│
├── main.py
├── README.md
├── requirements.txt
│
├── tools/
│   └── image_converter/
│       ├── run.py
│       └── README.md
│
└── .gitignore
```

- **main.py** → CLI Toolbox gateway
- **tools/** → contains all CLI tools
- **requirements.txt** → central dependency list for all tools

---

## Requirements

- Python **3.9 or newer**

To check if Python is already installed, run:

```bash
python --version
```

or:

```bash
python3 --version
```

---

## If Python Is Not Installed

Download Python from:

`https://www.python.org/downloads/`

During installation, make sure to enable:

```text
Add Python to PATH
```

If you need help adding Python to PATH, you may watch this tutorial (not my video):

`https://www.youtube.com/watch?v=pSIY82FwFkI`

---

## Setup and Run

### Step 1: Clone the repository

```bash
git clone https://github.com/YzrSaid/cli-toolbox.git
cd cli-toolbox
```

### Step 2: Install the required dependencies

```bash
pip install -r requirements.txt
```

This installs the libraries needed for all tools in the project.

### Step 3: Run CLI Toolbox

```bash
python main.py
```

If `python` does not work on your machine, try:

```bash
python3 main.py
```

---

## Optional: Virtual Environment

> **Note:** This step is mainly recommended for **Linux users** or for users who want to avoid problems with **Python package and dependency versions**.  
> Beginners on Windows can usually skip this if the project runs fine normally.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it.

### Linux / macOS

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Then install dependencies inside the virtual environment:

```bash
pip install -r requirements.txt
```

After that, run the project:

```bash
python main.py
```

---

## Developer

Created by **Mohammad Aldrin Said**

GitHub: `https://github.com/YzrSaid`
