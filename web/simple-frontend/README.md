# Simple HTML Frontend for Arcane Auditor

This is a lightweight, Node.js-free alternative to the React frontend. It provides the same core functionality using only HTML, CSS, and vanilla JavaScript.

## Features

- **File Upload**: Drag & drop or click to select ZIP files
- **Results Display**: Interactive filtering and sorting of findings
- **Excel Export**: Download results as Excel files
- **Responsive Design**: Works on desktop and mobile
- **No Dependencies**: Pure HTML/CSS/JavaScript - no build process required

## Comparison with React Frontend

| Feature | React Frontend | Simple HTML Frontend |
|---------|----------------|---------------------|
| **Dependencies** | Node.js, npm, React, Vite | None |
| **Build Process** | `npm install && npm run build` | None |
| **File Size** | ~500KB+ (bundled) | ~50KB (uncompressed) |
| **Development** | Hot reload, JSX, TypeScript | Direct HTML editing |
| **Security Risk** | npm supply chain vulnerabilities | Minimal |
| **Functionality** | Full featured | Core features only |
| **Maintenance** | Complex build pipeline | Simple file updates |

## Usage

1. **Start the server**:
   ```bash
   python web/simple_server.py --port 8080 --open-browser
   ```

2. **Open your browser** to `http://localhost:8080`

3. **Upload a ZIP file** containing your Workday Extend application

4. **View results** with filtering and sorting options

5. **Download Excel** export if needed

## File Structure

```
web/simple-frontend/
├── index.html          # Main HTML page
├── style.css           # All styling
├── script.js           # All JavaScript functionality
└── README.md           # This file
```

## API Endpoints

The simple server provides these endpoints:

- `GET /` - Serve the HTML interface
- `POST /api/analyze` - Analyze uploaded ZIP file
- `POST /api/download/excel` - Download Excel results
- `GET /api/rules` - Get available rules
- `GET /api/configs` - Get saved configurations
- `GET /api/config/{name}` - Get specific configuration
- `POST /api/config` - Save configuration

## Advantages

✅ **No Node.js required** - Eliminates supply chain risks  
✅ **Instant deployment** - No build process needed  
✅ **Easy to modify** - Direct HTML/CSS/JS editing  
✅ **Lightweight** - Minimal file size  
✅ **Self-contained** - All code in 3 files  
✅ **Fast loading** - No JavaScript framework overhead  

## Limitations

❌ **No hot reload** - Manual refresh required for changes  
❌ **No TypeScript** - Plain JavaScript only  
❌ **No component system** - Monolithic structure  
❌ **Limited interactivity** - Basic DOM manipulation  
❌ **No state management** - Simple global variables  

## When to Use

**Use Simple HTML Frontend when:**
- Security is a primary concern (no Node.js)
- You want minimal dependencies
- You need quick deployment
- You prefer simple, maintainable code
- You don't need advanced UI features

**Use React Frontend when:**
- You need advanced UI interactions
- You want modern development tools
- You're comfortable with Node.js
- You need component reusability
- You want TypeScript support

## Customization

To modify the interface:

1. **Styling**: Edit `style.css` for colors, layout, fonts
2. **Functionality**: Edit `script.js` for behavior changes
3. **Structure**: Edit `index.html` for layout modifications

All changes take effect immediately - no build process required!
