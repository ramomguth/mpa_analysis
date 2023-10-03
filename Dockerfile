# Use an official Python runtime as a base image
FROM python:3.11

# Set the working directory in the container to /app
WORKDIR /tcc

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for the Django secret key
ENV DJANGO_SECRET_KEY=your-secret-key-here

# Run gunicorn when the container launches
CMD ["gunicorn", "your_project_name.wsgi:application", "--bind", "0.0.0.0:8000"]
