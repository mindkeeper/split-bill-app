# Split Bill Backend API

A Python FastAPI backend service that processes bill/receipt images using Mistral's OCR capabilities to extract itemized information for bill splitting applications.

## Features

- 🖼️ **Image Upload & Processing**: Accept bill/receipt images in multiple formats (JPEG, PNG, WebP)
- 🤖 **Mistral OCR Integration**: Use Mistral's vision model for accurate text extraction
- 📊 **Structured Data Extraction**: Parse bills into structured JSON with items, prices, totals
- 🚀 **Fast API**: High-performance async API with automatic documentation
- 🐳 **Docker Ready**: Containerized for easy deployment
- 🧪 **Comprehensive Testing**: Full test suite with mocking
- 📝 **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Quick Start

### Prerequisites

- Python 3.11+
- Mistral AI API key ([Get one here](https://console.mistral.ai/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd split-bill-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your MISTRAL_API_KEY
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

   Or with uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health` | Health check endpoint |
| POST | `/process-bill` | Process single bill image with OCR |
| POST | `/process-multiple-bills` | Process multiple bill images with OCR |
| POST | `/upload-test` | Test file upload without processing |

### Process Single Bill Image

**POST** `/process-bill`

Upload and process a single bill/receipt image to extract structured data.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing the image

**Supported formats:** JPEG, PNG, WebP (max 10MB)

**Response:**
```json
{
  "status": "success",
  "message": "Bill processed successfully",
  "bill_info": {
    "restaurant_name": "Pizza Palace",
    "date": "2024-01-15",
    "time": "19:30",
    "items": [
      {
        "name": "Margherita Pizza",
        "price": 18.00,
        "quantity": 1
      },
      {
        "name": "Coca Cola",
        "price": 3.50,
        "quantity": 2
      }
    ],
    "subtotal": 25.00,
    "tax": 2.25,
    "tip": 5.00,
    "total": 32.25,
    "currency": "USD"
  },
  "raw_text": "Raw OCR extracted text...",
  "processing_time": 2.34,
  "timestamp": "2024-01-15T19:30:00Z"
}
```

### Process Multiple Bill Images

**POST** `/process-multiple-bills`

Upload and process multiple bill/receipt images simultaneously to extract structured data from each.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with multiple `files` fields containing the images
- **Limits:** Maximum 10 images per request, 10MB per image

**Supported formats:** JPEG, PNG, WebP

**Response:**
```json
{
  "status": "success",
  "message": "2/2 images processed successfully",
  "total_images": 2,
  "successful_images": 2,
  "failed_images": 0,
  "bills": [
    {
      "status": "success",
      "message": "Bill processed successfully",
      "bill_info": {
        "restaurant_name": "Pizza Palace",
        "date": "2024-01-15",
        "items": [...],
        "total": 32.25
      },
      "raw_text": "Raw OCR text...",
      "timestamp": "2024-01-15T19:30:00Z"
    },
    {
      "status": "success",
      "message": "Bill processed successfully",
      "bill_info": {
        "restaurant_name": "Burger King",
        "date": "2024-01-15",
        "items": [...],
        "total": 15.50
      },
      "raw_text": "Raw OCR text...",
      "timestamp": "2024-01-15T19:30:00Z"
    }
  ],
  "total_processing_time": 4.67,
  "timestamp": "2024-01-15T19:30:00Z",
  "errors": []
}
```

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Create .env file**
   ```bash
   cp .env.example .env
   # Add your MISTRAL_API_KEY
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

### Using Docker directly

1. **Build the image**
   ```bash
   docker build -t split-bill-backend .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name split-bill-backend \
     -p 8000:8000 \
     -e MISTRAL_API_KEY=your_api_key_here \
     split-bill-backend
   ```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_main.py
pytest test_mistral_service.py
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MISTRAL_API_KEY` | Mistral AI API key | - | ✅ |
| `HOST` | Server host | `0.0.0.0` | ❌ |
| `PORT` | Server port | `8000` | ❌ |
| `DEBUG` | Debug mode | `True` | ❌ |
| `MAX_FILE_SIZE_MB` | Max upload size | `10` | ❌ |
| `ALLOWED_FILE_TYPES` | Allowed MIME types | `image/jpeg,image/png,image/webp` | ❌ |

### File Upload Limits

- **Maximum file size**: 10MB
- **Supported formats**: JPEG, PNG, WebP
- **Processing timeout**: 30 seconds

## Project Structure

```
split-bill-backend/
├── main.py                 # FastAPI application
├── models.py              # Pydantic data models
├── mistral_service.py     # Mistral OCR integration
├── test_main.py           # API endpoint tests
├── test_mistral_service.py # Mistral service tests
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── .env.example         # Environment variables template
└── README.md           # This file
```

## API Usage Examples

### Using curl

```bash
# Upload and process a single bill image
curl -X POST "http://localhost:8000/process-bill" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@bill_image.jpg"

# Upload and process multiple bill images
curl -X POST "http://localhost:8000/process-multiple-bills" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@bill1.jpg" \
  -F "files=@bill2.jpg" \
  -F "files=@bill3.jpg"
```

### Using Python requests

```python
import requests

# Process single bill
url = "http://localhost:8000/process-bill"
files = {"file": open("bill_image.jpg", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"Status: {result['status']}")
print(f"Restaurant: {result['bill_info']['restaurant_name']}")
print(f"Total: ${result['bill_info']['total']}")

# Process multiple bills
url = "http://localhost:8000/process-multiple-bills"
files = [
    ("files", open("bill1.jpg", "rb")),
    ("files", open("bill2.jpg", "rb")),
    ("files", open("bill3.jpg", "rb"))
]

response = requests.post(url, files=files)
result = response.json()

print(f"Processed {result['successful_images']}/{result['total_images']} images")
for i, bill in enumerate(result['bills']):
    if bill['status'] == 'success':
        print(f"Bill {i+1}: {bill['bill_info']['restaurant_name']} - ${bill['bill_info']['total']}")

# Close files
for _, file_obj in files:
    file_obj.close()
```

### Using JavaScript/Fetch

```javascript
// Process single bill
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/process-bill', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Processing result:', data);
  if (data.status === 'success') {
    console.log('Restaurant:', data.bill_info.restaurant_name);
    console.log('Total:', data.bill_info.total);
  }
});

// Process multiple bills
const multiFormData = new FormData();
for (let i = 0; i < fileInput.files.length; i++) {
  multiFormData.append('files', fileInput.files[i]);
}

fetch('http://localhost:8000/process-multiple-bills', {
  method: 'POST',
  body: multiFormData
})
.then(response => response.json())
.then(data => {
  console.log(`Processed ${data.successful_images}/${data.total_images} images`);
  
  data.bills.forEach((bill, index) => {
    if (bill.status === 'success') {
      console.log(`Bill ${index + 1}:`, bill.bill_info.restaurant_name, '$' + bill.bill_info.total);
    }
  });
  
  if (data.errors.length > 0) {
    console.log('Errors:', data.errors);
  }
});
```

## Production Deployment

### Cloud Deployment Options

1. **Railway/Render/Heroku**
   - Connect your GitHub repository
   - Set `MISTRAL_API_KEY` environment variable
   - Deploy automatically

2. **AWS/GCP/Azure**
   - Use container services (ECS, Cloud Run, Container Instances)
   - Deploy the Docker image
   - Configure environment variables

3. **VPS/Dedicated Server**
   - Use Docker Compose with production profile
   - Set up reverse proxy (nginx)
   - Configure SSL certificates

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure logging and monitoring
- [ ] Set up health checks
- [ ] Configure rate limiting
- [ ] Set up backup and recovery

## Troubleshooting

### Common Issues

1. **"MISTRAL_API_KEY environment variable is required"**
   - Ensure you have set the `MISTRAL_API_KEY` in your `.env` file
   - Verify the API key is valid and has sufficient credits

2. **"Unsupported file type"**
   - Only JPEG, PNG, and WebP images are supported
   - Check the file's MIME type

3. **"File too large"**
   - Maximum file size is 10MB
   - Compress the image or adjust `MAX_FILE_SIZE_MB`

4. **OCR processing errors**
   - Ensure the image is clear and readable
   - Check Mistral API status and quotas
   - Verify network connectivity

### Logs

Check application logs for detailed error information:

```bash
# Docker logs
docker-compose logs -f split-bill-backend

# Direct execution logs
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation at `/docs`