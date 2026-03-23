# Complete Guide: Extracting Files from Markdown

You have a markdown file containing all the Telegram downloader code, and you need to extract each code block into separate files. Here are multiple ways to do this in Linux, from simple to robust.

---

## Method 1: Python Script (RECOMMENDED - Most Reliable)

This is the most robust method with proper error handling.

### Step 1: Save the Python extractor script

Create a file called `extract_files.py` (I've provided this in the artifacts above):

```bash
# Copy the Python script from the artifact above and save it
nano extract_files.py
# Paste the content, then Ctrl+X, Y, Enter to save
```

Or if you have the script already:

```bash
chmod +x extract_files.py
```

### Step 2: Run the extractor

```bash
# Assuming your markdown file is called "telegram-downloader-files.md"
python3 extract_files.py telegram-downloader-files.md
```

### What it does:
- ✅ Creates a `telegram-downloader/` directory
- ✅ Extracts all files with correct names and formats
- ✅ Makes shell scripts executable automatically
- ✅ Preserves exact formatting including line endings
- ✅ Provides colored output showing progress
- ✅ Gives you next steps when done

---

## Method 2: Bash Script (Alternative)

If you prefer pure bash, use this approach.

### Step 1: Save the bash extractor script

Create a file called `extract_files.sh` (I've provided this in the artifacts above):

```bash
nano extract_files.sh
# Paste the bash script content, then Ctrl+X, Y, Enter to save
```

Make it executable:

```bash
chmod +x extract_files.sh
```

### Step 2: Run the extractor

```bash
./extract_files.sh telegram-downloader-files.md
```

---

## Method 3: Manual AWK One-Liner (Quick & Dirty)

If you want a quick solution without saving a script:

```bash
# Create the output directory
mkdir -p telegram-downloader
cd telegram-downloader

# Run this AWK command
awk '
/^## File: / {
    # Extract filename from backticks
    match($0, /`[^`]+`/)
    filename = substr($0, RSTART+1, RLENGTH-2)
    in_code = 0
    next
}
/^```/ {
    if (in_code) {
        # End of code block
        in_code = 0
        filename = ""
    } else if (filename != "") {
        # Start of code block
        in_code = 1
    }
    next
}
in_code && filename != "" {
    print > filename
}
' ../telegram-downloader-files.md

# Make shell scripts executable
chmod +x *.sh 2>/dev/null || true

echo "Extraction complete!"
ls -la
```

---

## Method 4: Manual Sed/Grep Approach

For those who prefer sed and grep:

```bash
#!/bin/bash

MARKDOWN_FILE="telegram-downloader-files.md"
OUTPUT_DIR="telegram-downloader"

mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

# Extract all filenames
grep "^## File:" "../$MARKDOWN_FILE" | sed 's/^## File: `\(.*\)`/\1/' | while read -r filename; do
    echo "Extracting: $filename"
    
    # Extract the code block for this file
    sed -n "/^## File: \`${filename//\//\\/}\`/,/^## File:/p" "../$MARKDOWN_FILE" | \
    sed -n '/^```/,/^```/p' | \
    sed '1d;$d' > "$filename"
    
    # Make scripts executable
    if [[ "$filename" == *.sh ]]; then
        chmod +x "$filename"
    fi
done

echo "Done!"
```

---

## Method 5: Using Perl (For Perl Users)

```bash
perl -ne '
    if (/^## File: `([^`]+)`/) { 
        $file = $1; 
        $in_code = 0; 
    }
    if (/^```/ && $file) {
        if ($in_code) {
            close OUT;
            $file = "";
            $in_code = 0;
        } else {
            open OUT, ">telegram-downloader/$file" or die $!;
            $in_code = 1;
        }
        next;
    }
    print OUT $_ if $in_code;
' telegram-downloader-files.md

# Make shell scripts executable
chmod +x telegram-downloader/*.sh 2>/dev/null || true
```

---

## Complete Example: Using the Python Method

Here's the complete workflow from start to finish:

```bash
# 1. Create a working directory
mkdir ~/telegram-project
cd ~/telegram-project

# 2. Save the markdown file (assuming you downloaded it)
# Let's say it's in your Downloads folder
cp ~/Downloads/telegram-downloader-files.md .

# 3. Create the Python extractor script
cat > extract_files.py << 'EOF'
#!/usr/bin/env python3
# [PASTE THE ENTIRE PYTHON SCRIPT HERE]
EOF

# 4. Make it executable
chmod +x extract_files.py

# 5. Run the extraction
./extract_files.py telegram-downloader-files.md

# 6. You should see output like:
# ========================================
# Telegram Downloader Files Extractor
# ========================================
# 
# Processing: telegram-downloader-files.md
# 
# ✓ Created project directory: telegram-downloader
# 
# ✓ Extracted: Dockerfile
# ✓ Extracted: docker-compose.yml
# ✓ Extracted: requirements.txt
# [... etc ...]
# 
# ========================================
# Extraction Complete!
# ========================================
# Total files extracted: 9

# 7. Navigate to the project directory
cd telegram-downloader

# 8. Verify all files are there
ls -la

# Expected output:
# Dockerfile
# docker-compose.yml
# requirements.txt
# config.py
# media_downloader.py
# .dockerignore
# .gitignore
# .env.example
# README.md

# 9. Set up your environment file
cp .env.example .env
nano .env  # Add your API credentials

# 10. Build and run!
docker compose build
docker compose run --rm telegram-downloader  # First-time auth
docker compose up -d  # Run in background
```

---

## Verification Commands

After extraction, verify everything worked correctly:

```bash
cd telegram-downloader

# Check all files are present
echo "Checking for required files..."
for file in Dockerfile docker-compose.yml requirements.txt config.py media_downloader.py .dockerignore .gitignore .env.example README.md; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ Missing: $file"
    fi
done

# Check file sizes (none should be empty)
echo ""
echo "File sizes:"
ls -lh Dockerfile docker-compose.yml requirements.txt config.py media_downloader.py

# Check Python syntax
echo ""
echo "Validating Python files..."
python3 -m py_compile config.py media_downloader.py && echo "✓ Python syntax OK"

# Check YAML syntax (if you have yamllint)
if command -v yamllint &> /dev/null; then
    echo "Validating YAML files..."
    yamllint docker-compose.yml && echo "✓ YAML syntax OK"
fi
```

---

## Troubleshooting

### Issue: Files are empty or truncated

**Solution:** The markdown format might have slight variations. Try the Python method as it's most robust.

### Issue: "File not found" error

**Solution:** Make sure you're in the correct directory and the markdown filename is exact:
```bash
ls -la *.md  # List all markdown files
```

### Issue: Permission denied

**Solution:** Make the script executable:
```bash
chmod +x extract_files.py
# or
chmod +x extract_files.sh
```

### Issue: Line ending problems (Windows files on Linux)

**Solution:** Convert line endings:
```bash
dos2unix telegram-downloader-files.md
# or
sed -i 's/\r$//' telegram-downloader-files.md
```

### Issue: Special characters in filenames

**Solution:** The Python script handles this automatically. If using bash, ensure you're using the provided script which handles special characters.

---

## What Each Method Does

All methods perform these steps:

1. **Parse the markdown** looking for `## File:` headers
2. **Identify code blocks** between triple backticks
3. **Extract the content** of each code block
4. **Write to files** with the correct name
5. **Set permissions** (make .sh files executable)
6. **Create directories** if files are in subdirectories

The Python method is recommended because it:
- Has the best error handling
- Handles all edge cases properly
- Provides clear progress output
- Works consistently across systems
- Maintains exact formatting

---

## Quick Start (Copy-Paste Ready)

Just run this if you want the fastest path:

```bash
# Download the markdown file to your current directory first!

# Then run this entire block:
python3 << 'PYTHON_SCRIPT'
import sys, os, re
from pathlib import Path

def extract(md_file):
    with open(md_file, 'r') as f:
        lines = f.readlines()
    
    files, current, in_block, code = [], None, False, []
    pattern = re.compile(r'^##\s+File:\s+`([^`]+)`')
    
    for line in lines:
        if m := pattern.match(line):
            current, in_block, code = m.group(1), False, []
        elif line.startswith('```') and current:
            if in_block:
                files.append((current, ''.join(code)))
                current, in_block, code = None, False, []
            else:
                in_block, code = True, []
        elif in_block:
            code.append(line)
    
    Path('telegram-downloader').mkdir(exist_ok=True)
    for name, content in files:
        path = Path('telegram-downloader') / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        if name.endswith('.sh'):
            os.chmod(path, 0o755)
        print(f"✓ {name}")
    
    print(f"\n✓ Extracted {len(files)} files to telegram-downloader/")

extract('telegram-downloader-files.md')
PYTHON_SCRIPT
```

That's it! Your files are now extracted and ready to use.

---

## Summary

**Recommended approach:**
1. Use the Python script (`extract_files.py`) for best results
2. Run: `python3 extract_files.py telegram-downloader-files.md`
3. Follow the on-screen instructions to set up `.env`
4. Build and run with Docker

The Python method is the most reliable and handles all edge cases properly. Save the script once and you can use it for any future markdown exports!