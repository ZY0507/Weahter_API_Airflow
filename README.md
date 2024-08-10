### Setting Up Your Linux Virtual Machine for the Project

1. **Choose a Cloud Provider**:
   - To run this project, you'll need a Linux virtual machine (VM) on a cloud platform. You can use services like **Azure Virtual Machines**, **AWS EC2**, or **Google Cloud Platform (GCP) Compute Engine**.
   - **Important**: Make sure the VM has **at least 4GB of memory** to handle the project.

2. **Initial VM Configuration**:
   - **Create a Key Pair**: When you first set up your VM, you'll need to create a key pair. This key pair allows you to securely connect to the VM and use a graphical interface if needed.
   - **Allow HTTPS Traffic**: Ensure that your VM is set up to allow HTTPS traffic from the internet.
   - **Set Up Inbound Rules**:
     - For AWS EC2: 
       1. Go to **Security Groups**.
       2. Find the one with a name starting with "sg...".
       3. Click **Edit Inbound Rules**.
       4. **Add a Rule**: Set **Port Range** to `8080` and **Source** to `Anywhere-IPv4`.

3. **Connect to Your VM and Install Necessary Applications**:
   - **Update Your VM**:
     ```bash
     sudo apt update
     ```
   - **Install Python and Pip**:
     ```bash
     sudo apt install python3-pip
     sudo apt install python3-venv
     ```
   - **Create an Airflow Virtual Environment**:
     ```bash
     python3 -m venv airflow_venv
     source airflow_venv/bin/activate
     ```
   - **Install Additional Applications**:
     - Inside the virtual environment:
     ```bash
     sudo apt install python3-pandas
     pip3 install s3fs apache-airflow pyarrow
     airflow standalone
     ```

4. **Access the Airflow GUI**:
   1. Copy the IPv4 address of your VM.
   2. Add `:8080` at the end of the address and enter it in your web browser.
   3. The username and password for Airflow will be shown when you run `airflow standalone` in your VM.
   4. In the Airflow GUI, go to **Admin -> Connections**.
   5. Add a new record with the following:
      - **Connection Id**: Weather_API
      - **Connection Type**: HTTP
      - **Host**: http://api.weatherapi.com

5. **Connect to Linux GUI via VS Code**:
   1. **Download the Key Pair** you created earlier.
   2. In AWS EC2, go to **Instances** and select your instance.
   3. Click **Connect** and choose **SSH client**. Copy the SSH command that starts with `ssh`.
   4. Open Command Prompt or PowerShell and paste the SSH command. Type `yes` when prompted.
   5. Open VS Code and install the extension **Remote - SSH**.
   6. Click **Open a Remote Window** (bottom left in VS Code) -> **Connect to Host** -> **Configure SSH Hosts**.
   7. Choose `C:/Users/your_user_name/.ssh/config`.
   8. Fill in the configuration with the following:
      - **Host**: Your EC2 name (e.g., WeatherAPIAirflow)
      - **HostName**: The IP address of your VM
      - **User**: `ubuntu`
      - **IdentityFile**: The path to your downloaded key pair file
   9. Click **Open a Remote Window** -> **Connect to Host** -> choose your EC2 name.
   10. In the VS Code Explorer, open your Linux file path.
   11. Create a folder called `dags` under `airflow`, then create a Python file named `weather_dag.py` inside it.

6. **Create an S3 Bucket**:
   1. Search for **S3** in your cloud provider's dashboard.
   2. Create a bucket with a unique, lowercase name.
   3. In AWS EC2, click on your instance, go to **Actions -> Security - Modify IAM role**.
   4. Create a new IAM role:
      - Select **AWS Service -> EC2 -> Next**.
      - Search and attach `AmazonEC2FullAccess` and `AmazonS3FullAccess` policies.
      - Provide a role name, create, and choose it.

7. **Get Credentials for S3**:
   1. Click on your username in the cloud dashboard and go to **Security Credentials**.
   2. Create an access key and store the key and secret access key in a secure file.
   3. In your VM, run:
      ```bash
      sudo apt install awscli
      ```
   4. Configure AWS CLI with:
      ```bash
      aws configure
      ```
   5. Type `aws sts get-session-token` to get temporary credentials.
   6. Replace the `key`, `secret`, and `token` in your script with these new credentials.

8. **Running Airflow**:
   - Your Airflow setup is now complete! You can run your workflow manually or schedule it to run at specific intervals.
