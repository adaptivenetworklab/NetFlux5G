# 🐳 Container Technology Comparison: Docker vs Containerd vs Podman vs LXD

## 📘 Overview
This repository contains a comprehensive test suite for comparing four popular container technologies on **Ubuntu 22.04**:

- **Docker**
- **Containerd** (with `nerdctl`)
- **Podman**
- **LXD**

The suite evaluates performance, security, usability, and features to help you select the right technology for your environment.

## 📁 Repository Structure

container-tech-comparison/
├── README.md                            # Main documentation (this file)
├── install.sh                           # Installation script for all technologies
├── run\_all\_tests.sh                     # Main script to run all tests
├── tests/                               # Directory containing all test scripts
│   ├── container\_operations.sh
│   ├── resource\_isolation.sh
│   ├── container\_stress\_test.sh
│   ├── performance\_test.sh
│   ├── io\_performance\_test.sh
│   ├── network\_performance\_test.sh
│   ├── security\_comparison.sh
│   ├── startup\_time\_test.sh
│   ├── runtime\_overhead\_test.sh
│   ├── multi\_container\_test.sh
│   ├── build\_performance\_test.sh
│   ├── storage\_driver\_test.sh
│   ├── sysbench\_stress\_test.sh
│   ├── application\_deployment\_test.sh
│   ├── monitoring\_logging\_comparison.sh
│   └── update\_versioning\_test.sh
├── utils/                               # Utility scripts and helpers
│   ├── common\_functions.sh
│   ├── generate\_report.sh
│   ├── setup\_test\_environment.sh
│   └── cleanup.sh
├── docs/                                # Documentation files
│   ├── container\_best\_practices.md
│   ├── installation\_guide.md
│   ├── test\_methodology.md
│   └── interpretation\_guide.md
├── templates/                           # Test templates
│   ├── Dockerfile.test
│   ├── docker-compose.yml
│   ├── podman-pod.yml
│   ├── lxd-profile.yaml
│   └── app/
│       ├── app.py
│       └── requirements.txt
└── results/                             # Generated test results
├── raw/
├── processed/
├── summary\_report.md
└── index.html

## ✅ Prerequisites

Ensure your system meets the following requirements:

- Ubuntu 22.04 LTS
- Sudo privileges
- Internet connection
- At least **10GB** of free disk space
- **4GB+ RAM** recommended

---

## ⚙️ Installation

Run the setup script to install all required container technologies and tools:

```bash
sudo ./install.sh
````

This installs:

* Docker
* Containerd + `nerdctl`
* Podman
* LXD
* Supporting tools: `stress-ng`, `sysbench`, etc.

> ⚠️ **Note:** After installation, log out and back in for group permissions to take effect.

---

## 🚀 Running Tests

### Run All Tests

To run the full test suite:

```bash
./run_all_tests.sh

This will:

* Run all test scripts sequentially
* Save raw and processed results under the `results/` directory
* Generate reports in Markdown and HTML formats

### Run Individual Test

Example: Run only the performance test

```bash
./tests/performance_test.sh
```

---

## 📊 Test Categories

The suite includes the following categories:

| Category              | Description                                       |
| --------------------- | ------------------------------------------------- |
| **Basic Operations**  | Create, start, stop, remove containers            |
| **Resource Mgmt**     | CPU/memory limits, cgroups, namespaces            |
| **Performance**       | CPU, memory, disk I/O, and network performance    |
| **Build Process**     | Image build time and efficiency                   |
| **Multi-Container**   | Managing pods, multiple containers, orchestration |
| **Security**          | Isolation, AppArmor, SELinux, user namespaces     |
| **Monitoring & Logs** | Integration with logging and monitoring tools     |
| **App Deployment**    | Test deployment of real-world apps                |
| **Storage Drivers**   | Driver performance, volume handling               |
| **Update Handling**   | Image versioning and update strategies            |

---

## 📂 Viewing Results

After running tests:

* View **interactive HTML report** at: `results/index.html`
* Read **Markdown summary report** at: `results/summary_report.md`
* Inspect **raw test logs** in: `results/raw/`

---

## ⚙️ Customizing Tests

All test scripts include variables at the top that you can edit to customize behavior, such as:

* Container image
* Resource limits
* Duration of stress tests

---

## 📚 Documentation

Additional guides are available in the `docs/` folder:

* `container_best_practices.md` — Optimizing usage for each technology
* `installation_guide.md` — Manual installation steps
* `test_methodology.md` — Explanation of testing strategy
* `interpretation_guide.md` — Understanding and comparing results

---

## 🤝 Contributing

We welcome community contributions!

* Fork the repository
* Create a new branch
* Submit a Pull Request

For bugs, feature suggestions, or questions, please open an issue.

---

## 🪪 License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

* Docker, Containerd, Podman, and LXD communities for excellent documentation
* Developers of tools used: `stress-ng`, `sysbench`, `iperf3`, etc.
* Ubuntu for providing a great base OS for testing

---

## 📬 Contact

Have questions or suggestions?
Feel free to open an [issue](https://github.com/your-repo/issues) in this repository.
