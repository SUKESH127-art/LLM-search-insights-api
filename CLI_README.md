# 🚀 LLM Search Insight API - CLI Tools

Beautiful command-line interface for analyzing research questions using the LLM Search Insight API with MCP integration.

## ✨ Features

- 🎨 **Beautiful Output**: Color-coded, formatted results with progress bars
- 📊 **Real-time Progress**: Live progress monitoring with step-by-step updates
- 🔍 **MCP Integration**: Leverages BrightData MCP for real-time web data
- 🤖 **AI Analysis**: Combines web search with ChatGPT insights
- 📱 **Simple Usage**: Just one parameter - your research question

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Make Scripts Executable**:
   ```bash
   chmod +x analyze.py
   chmod +x analyze
   ```

## 🚀 Usage

### Method 1: Direct Python Script
```bash
python3 analyze.py "Your research question here"
```

### Method 2: Simple Alias Script
```bash
./analyze "Your research question here"
```

## 📝 Examples

### **Technology Research**
```bash
./analyze "What are the best frontend frameworks for 2024?"
```

### Machine Learning Trends
```bash
./analyze "What are the latest trends in machine learning for 2024?"
```

### Database Options
```bash
./analyze "What are the best database options for a Node.js backend?"
```

## 🎯 What You Get

### 1. **Web Analysis** (via BrightData MCP)
- Real-time web data extraction
- Source attribution
- Confidence scoring
- Fallback handling for errors

### 2. **ChatGPT Analysis**
- AI-powered insights
- Brand identification
- Structured recommendations
- Context-aware responses

### 3. **Visualization Data**
- Chart type information
- Data summaries
- Progress tracking

## 🔧 Prerequisites

1. **API Server Running**: 
   ```bash
   python3 main.py
   ```

2. **Environment Variables** (in `.env`):
   - `OPENAI_API_KEY`
   - `BRIGHTDATA_API_KEY`

3. **Dependencies**: All packages in `requirements.txt`

## 🎨 Output Features

- **Progress Bars**: Visual progress tracking with █ characters
- **Color Coding**: 
  - 🔵 Blue: Information steps
  - 🟢 Green: Success messages
  - 🟡 Yellow: Warnings
  - 🔴 Red: Errors
- **Formatted Results**: Clean, readable output sections
- **Real-time Updates**: Live progress monitoring

## 🚨 Error Handling

- **Server Connection**: Checks if API server is running
- **API Errors**: Graceful handling of quota limits and errors
- **Fallback Data**: Provides useful information even when APIs fail
- **Clear Messages**: User-friendly error descriptions

## 🔄 Workflow

1. **Submit**: Sends research question to API
2. **Monitor**: Tracks analysis progress in real-time
3. **Retrieve**: Gets final analysis results
4. **Display**: Shows formatted, beautiful output

## 💡 Tips

- **Use Quotes**: Always wrap your question in quotes
- **Be Specific**: More specific questions get better results
- **Check Server**: Ensure `python3 main.py` is running
- **Monitor Progress**: Watch the progress bar for real-time updates

## 🐛 Troubleshooting

### "Cannot connect to API server"
- Make sure `python3 main.py` is running
- Check if port 8000 is available

### "Module not found"
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### "Quota exceeded"
- This is normal - the system provides fallback data
- MCP integration will work once quota is restored

## 🎉 Success!

Your CLI is now ready to provide beautiful, real-time analysis of any research question with MCP integration!
