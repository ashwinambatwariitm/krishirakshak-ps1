# Bharat AI-SoC Challenge 2026-27

## Official source

- **Challenge page:** <https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html>
- **Information captured:** 1 November 2026
- **Important:** This file is a locally saved reference. The official webpage is the authoritative source for later updates, clarifications, and organiser announcements.

## Quick summary

The Bharat AI-SoC Challenge 2026-27 is the second edition of a nationwide challenge organised by **Arm** through the **Chips to Startup (C2S) Programme** of the Ministry of Electronics & Information Technology (MeitY), with **IIT Delhi** as the mentor institute. The initiative is supported by the UK Government through the **UK-India Technology Security Initiative (TSI)**.

The challenge focuses on **applied AI on Arm-based systems-on-chip (SoCs)**. Participants must move beyond building a cloud-connected AI application and demonstrate an AI-enabled product engineered for the edge, including optimisation, system integration, deployment, benchmarking, validation, and product engineering.

Participants can choose one of five problem statements. The challenge requires the use of a **Llama-family model** and **ExecuTorch** for the advisory or reasoning component. Solutions are expected to run on-device, with local processing supporting real-time operation, privacy, offline use, and consideration of performance, power, and cost.

## Challenge history and context

The inaugural Bharat AI-SoC Student Challenge was organised by Arm, MeitY C2S, and IIT Delhi. It attracted:

- More than 3,000 students
- 1,238 teams
- Three levels of evaluation and virtual mentorship
- 150 shortlisted teams
- Five winners

The second edition expands participation to both students and working professionals/developers. These categories compete on equal terms across all five problem statements.

## What is new in the second edition?

### Participant categories

- Students at undergraduate or postgraduate level
- Working professionals and developers

### Two challenge phases

1. **Open Qualifying:** Participants submit an initial solution, report, source code, and demo.
2. **PoC Development:** Shortlisted teams receive mentorship and develop a complete proof of concept.

### Winners

One winning team is selected for each problem statement after the final live virtual demonstration and jury question-and-answer session.

## Technology theme: Applied AI on SoC

Applied AI on SoC means bringing AI processing onto an edge device rather than depending on a remote cloud service. The intended benefits include:

- Real-time operation
- Privacy-aware processing
- Offline capability
- Reduced dependence on network connectivity
- Better control over performance, power, and cost

The engineering journey covered by the challenge includes:

1. AI algorithm development
2. Model and application optimisation
3. System integration
4. Edge deployment
5. Benchmarking
6. Validation
7. Product engineering

## Required technology

Every problem statement requires:

- **Llama**
- **ExecuTorch**

### Technical requirement

A model from the **Llama family** must be used for the advisory or reasoning component and deployed on-device using **ExecuTorch** as the reference runtime.

Examples given on the official page include:

- Llama 3.2 1B Instruct
- Llama 3.2 3B Instruct
- A fine-tuned Llama variant
- A distilled Llama variant

The implementation should clearly demonstrate where Llama is used and how ExecuTorch performs the on-device deployment.

## Challenge phases and submissions

### Phase 1 - Open Qualifying

- **Submission deadline:** 23 November 2026
- Teams develop their initial solution.
- Required submission items include:
  - Project report
  - Source code
  - Demonstration

### Phase 2 - PoC Development

- **Submission deadline:** 5 February 2027
- Only shortlisted teams advance.
- Shortlisted teams receive mentorship to develop and complete their proof of concept.

## Problem statements

All eligible participants may choose any one of the five problem statements. A team may enter only one problem statement.

---

## PS1 - Offline crop-disease/pest detection and advisory for farmers

**Theme:** Agriculture & Food Security

### Objective

Develop an AI-powered assistant that helps farmers identify crop diseases, detect pests, and receive actionable recommendations. The system must operate entirely on-device without internet connectivity.

### Expected capabilities

The system should be able to analyse crop images to:

- Detect diseases and pests
- Classify severity levels
- Recommend treatment and intervention strategies
- Provide region-specific advisory guidance
- Support multiple local languages
- Operate offline for rural communities with limited connectivity

### Example application areas

- Crop disease early warning
- Pest identification and management
- Fertiliser and irrigation advisory
- Post-harvest loss reduction
- Smallholder farmer decision support
- Agri-extension worker tools

### Suitable hardware

Teams may use any suitable Arm-based platform, including:

- Arm-based Android smartphones
- Raspberry Pi 5 running CPU-only
- Raspberry Pi 5 with AI HAT+ or AI HAT+ 2
- Other Arm-based Linux devices

### Accelerator and pipeline guidance

If a Hailo accelerator is used for vision workloads:

- Vision models run through **HailoRT** on the Hailo NPU.
- Llama runs through **ExecuTorch** on the Raspberry Pi Arm CPU.
- These are separate pipelines and must be clearly documented.

### Optional technologies and resources

- OpenCV
- Hailo SDK
- PlantVillage dataset
- Cassava dataset
- IP102 dataset
- Speech-processing frameworks for voice-based advisory
- Multilingual NLP models

### Deliverables

- Source code
- Application
- Demonstration video
- Technical report

---

## PS2 - Smart recycling and waste-segregation assistant using multimodal interfaces

**Theme:** Environment & Climate

### Objective

Develop an AI-powered assistant that helps users identify, classify, and properly dispose of waste materials using Llama and ExecuTorch on Arm-based devices.

### Expected capabilities

- Identify waste categories
- Provide disposal recommendations
- Explain recycling options
- Promote sustainable waste-management practices
- Educate users about environmental impact

Teams may design the user experience most appropriate for their solution.

### Possible interfaces

- Android application
- Chat-based assistant
- Voice-based assistant
- Camera-enabled assistant
- WhatsApp integration
- Multimodal AI experience

### Example application areas

- Household recycling
- E-waste management
- Community recycling
- Plastic waste reduction
- Sustainability education

### Suitable hardware

- Arm-based Android smartphones
- Raspberry Pi 5 running CPU-only
- Raspberry Pi 5 with AI HAT+ or AI HAT+ 2
- Other Arm-based Linux devices

If a Hailo accelerator is used for vision workloads, vision models run through HailoRT on the Hailo NPU while Llama runs through ExecuTorch on the Raspberry Pi Arm CPU. The two pipelines must be documented separately.

### Optional technologies

- OpenCV
- Hailo SDK
- Speech-processing frameworks
- Computer-vision models

### Functional requirements

- Classify waste materials
- Provide disposal recommendations
- Explain recycling options
- Demonstrate use of Llama
- Demonstrate use of ExecuTorch

### Deliverables

- Source code
- Application or interface
- Demonstration video
- Technical report

---

## PS3 - On-device threat, phishing, and scam detection

**Theme:** Cybersecurity & Digital Safety

### Objective

Develop an on-device AI system that detects cybersecurity threats, including network intrusions, malware behaviour, phishing, and scam communications. The system must run on Arm-based edge hardware without cloud dependency.

### Expected capabilities

- Monitor and classify network traffic for anomalies and intrusions
- Detect phishing URLs
- Detect scam SMS messages and fraudulent communications
- Explain threats to non-expert users in plain language
- Recommend remediation actions
- Process data locally without relying on cloud services

### Example application areas

- Home and small-to-medium enterprise network intrusion detection
- Scam-call and SMS filtering
- Phishing-link detection
- IoT device behaviour monitoring
- Offline threat intelligence for air-gapped systems
- Digital-safety assistant for non-technical users

### Suitable hardware

- Arm-based Android smartphones
- Raspberry Pi 5 running CPU-only
- Raspberry Pi 5 with AI HAT+ or AI HAT+ 2
- Other Arm-based Linux devices

For compatible workloads using a Hailo accelerator, the Hailo pipeline runs through HailoRT on the Hailo NPU, while Llama runs through ExecuTorch on the Raspberry Pi Arm CPU. These pipelines must be clearly documented.

### Optional technologies and resources

- CICIDS dataset
- UNSW-NB15 dataset
- NSL-KDD dataset
- PhishTank feeds
- OpenPhish feeds
- UCI SMS Spam Collection
- `libpcap`
- Scapy
- Hailo SDK

### Deliverables

- Source code
- Application
- Demonstration video
- Technical report

---

## PS4 - On-device personalised learning assistant

**Theme:** Education

### Objective

Develop an AI learning companion that creates personalised learning pathways based on a learner's goals, interests, and current skill level.

### Expected capabilities

- Understand learner goals
- Identify skill gaps
- Recommend learning pathways
- Generate study plans
- Adapt recommendations over time

### Example application areas

- Career guidance
- Skill development
- Exam preparation
- Professional certification pathways
- Technical learning roadmaps
- Lifelong learning plans

### Required technologies and hardware

- Llama
- ExecuTorch
- Arm-based Android smartphone

The Llama-family model must provide the advisory or reasoning component and must be deployed on-device using ExecuTorch.

### Deliverables

- Source code
- Application
- Demonstration video
- Technical report

---

## PS5 - Real-time industrial defect detection and quality-control assistant

**Theme:** Manufacturing & Industry 4.0

### Objective

Develop an on-device AI system that performs real-time visual inspection of manufactured components, detects surface defects and anomalies, and assists quality-control operators on the factory floor.

### Expected capabilities

- Detect surface defects, cracks, and anomalies
- Classify defect type and severity
- Alert operators with actionable recommendations
- Log inspection results
- Operate in real time at the edge without cloud dependence

### Example application areas

- Printed circuit board inspection
- Steel and metal surface-defect detection
- Textile and fabric quality control
- Packaging integrity verification
- Automotive component inspection
- Pharmaceutical tablet and capsule inspection

### Suitable hardware

- Raspberry Pi 5 running CPU-only
- Raspberry Pi 5 with AI HAT+ or AI HAT+ 2
- Arm-based Linux devices
- Arm-based Android devices with a camera

If a Hailo accelerator is used for vision workloads, vision models run through HailoRT on the Hailo NPU while Llama runs through ExecuTorch on the Raspberry Pi Arm CPU. These are separate pipelines and should be clearly documented.

### Optional technologies and resources

- OpenCV
- Hailo SDK
- MVTec AD dataset
- NEU Surface Defect dataset
- KolektorSDD dataset
- YOLO
- EfficientDet
- Anomaly-detection frameworks

### Deliverables

- Source code
- Application
- Demonstration video
- Technical report

## Eligibility criteria

- Participants must be Indian nationals.
- Students must be nominated by their respective college.
- Teams may contain 1-3 members.
- All members of a student team must be from the same college.
- All members of a professional/developer team must be from the same organisation.
- Every team must have a Team Leader.
- Every student team must also have a Faculty Mentor.

## Official timeline

| Milestone | Date | Activities |
|---|---|---|
| Launch | 19 September 2026 | The Bharat AI-SoC Challenge 2026-27 launches. |
| Registration closes | 19 October 2026 | Eligible participants must complete registration by this date. |
| Phase 1 - Open Qualifying submission deadline | 23 November 2026 | Teams submit their Phase 1 project. |
| Phase 1 shortlisted-team results | Mid-December 2026 | Shortlisted teams are announced and advance to PoC Development. |
| Phase 2 - PoC Development submission deadline | 5 February 2027 | Shortlisted teams submit their proof of concept. |
| Finals and winners' announcement | 15-16 February 2027 | Final evaluation takes place; one winner is selected for each problem statement. |

## Registration status

Registration closed on **19 October 2026**. The official page states that the registration period for the Bharat AI-SoC Challenge has ended.

## Challenge guidelines and terms

- Only eligible students and working professionals/developers may participate.
- Only the Team Leader should register the team.
- Duplicate registrations may result in rejection or disqualification.
- All registration details must be accurate.
- Virtual mentoring is provided by industry and academic experts.
- Student teams may also receive local support from college mentors.
- Teams may contact mentors and experts by email.
- The project must be hosted on GitHub and submitted using the challenge submission form.
- Challenge-related notifications and updates are posted on the official challenge page.
- Winners must provide an appropriate college or organisation ID and supporting documents.
- Winner selection is at the sole discretion of the challenge organisers.
- Incorrect or duplicate entries may result in disqualification.

## Original-work and intellectual-property requirements

Entries must:

- Be the original work of the entrant or entrants.
- Be solely owned by the entrant or entrants.
- Not violate the intellectual-property rights of another person or entity.

Participants are responsible for ensuring that they have all necessary rights, permissions, and authorisations for any software, code, data, materials, or other content submitted as part of the challenge.

Participants must not submit or disclose confidential, proprietary, or third-party information unless they are authorised to do so and the disclosure does not breach a confidentiality, employment, contractual, or other obligation.

Participation does not require participants to disclose their own confidential information. Any participant materials voluntarily submitted or disclosed are provided at the participant's own discretion and responsibility.

Each participant remains responsible for ensuring that their submission does not infringe, misappropriate, or otherwise violate third-party intellectual-property or other rights.

## Support and resources

- **General support:** [support@armbharatchallenge.com](mailto:support@armbharatchallenge.com)
- **Technical questions:** [tech-queries@armbharatchallenge.com](mailto:tech-queries@armbharatchallenge.com)
  - Include the relevant problem-statement number in the subject line.
- **Getting Started Resources:** <https://arm-education.github.io/online-resources-arm/>
- **ExecuTorch course:** <https://learn.arm.com/courses/executorch-on-arm/>
- **First-edition details:** <https://www.armbharatchallenge.com/edition1>

Challenge updates are posted on the official challenge page:

<https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html>

## Rewards and recognition

| Recognition | Recipients | Reward |
|---|---|---|
| Winner | Each winning team | Cash award from IIT Delhi |
| Certificates | All team members who submit completed projects | Certificate |
| Finalist recognition | All finalists | Branded programme mementoes |

## Organising partners

| Category | Partner | Role |
|---|---|---|
| Government | MeitY and UK Government | MeitY is the Indian Government partner. The initiative is supported by the UK Government through the UK-India Technology Security Initiative (TSI). |
| Academia | IIT Delhi | Lead academic mentor for the challenge. |
| Industry | Arm, with support from Meta | Industry mentorship, technical guidance, and evaluation support. |

## Frequently asked questions

### Who can participate?

Indian nationals who meet the eligibility criteria may participate.

### How many people can be in a team?

Teams may have 1-3 members.

### Can students from different institutions form a team?

No. All members of a student team must be from the same college.

### Do student teams need a Faculty Mentor?

Yes. Each student team must have a Faculty Mentor.

### Can professionals from different organisations form a team?

No. All members of a professional/developer team must be from the same organisation.

### Can a team change its composition or challenge area?

One change of team composition or challenge area is permitted within 15 days of registration.

### Can a team enter more than one problem statement?

No. A team may enter only one of the five problem statements.

### Who are the organisers?

The challenge is led by Arm, with IIT Delhi as the mentor institute. MeitY is the Indian Government partner, and the initiative is supported by the UK Government through the UK-India Technology Security Initiative. Arm participates with support from Meta.

## Page-change reminder

Before making a submission or relying on a deadline, check the official page directly:

<https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html>

