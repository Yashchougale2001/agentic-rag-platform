# IT Security Policy

## 1. Scope
This policy applies to **all** company‑owned, leased, or contracted IT assets — including on‑premises servers, workstations, cloud workloads, and approved SaaS applications — regardless of where they are hosted or managed.

## 2. Multi‑Factor Authentication (MFA)
- MFA is required for **all** company systems and applications.  
- Approved methods: authenticator apps, hardware tokens, biometrics.  
- **SMS‑based MFA is discouraged for sensitive systems.**  
- Lost or compromised MFA devices must be reported **immediately** via the Security Incident Management System (SIMS); the device will be revoked and a replacement issued.

## 3. Encryption
- **Data‑at‑Rest:** AES‑256 encryption on all devices, storage media, and backups (separate key‑management for backup keys).  
- **Data‑in‑Transit:** TLS 1.2 or higher for all communications.  
- Data classification (Public, Internal, Confidential, Restricted) dictates that **Restricted** data must always be encrypted both at rest and in transit.

## 4. Antivirus & Endpoint Protection
- Must be installed on all company devices.  
- Real‑time scanning **must remain enabled**.  
- Virus‑definition updates are fetched **daily** (minimum).  
- Users **must not** disable or bypass the endpoint protection agent.  
- All security events are logged and retained for **90 days** for SIEM analysis.

## 5. Patch Management
### 5.1 Priority & Timeframe
| Priority | Timeframe to remediate |
|----------|------------------------|
| Critical | ≤ 48 hours |
| High     | ≤ 7 days |
| Medium   | ≤ 30 days |
| Low      | Next scheduled maintenance window |
### 5.2 Process
- Automatic updates are enabled where possible.  
- Systems must **reboot promptly** after patch installation.  
- Patch status is reported weekly to the IT Security Dashboard.

## 6. Access Control
- Least‑privilege principle enforced for all access.  
- Access reviews are conducted **quarterly**.  
- Inactive accounts are disabled after **30 days** of inactivity.  
- Termination of employment triggers **immediate** revocation of all access.  
- BYOD devices are subject to the same MFA and encryption requirements when accessing corporate resources.

## 7. Network Security
- Firewalls protect all network perimeters.  
- Remote access **requires** a VPN connection.  
- Public Wi‑Fi connections **must** use the corporate VPN.  
- Sensitive systems are isolated in **network segments** with strict ACLs.  

## 8. Incident Reporting & Response
- Any suspected security incident must be reported via SIMS within **1 hour**.  
- The IT Security team initiates the Incident Response Playbook, which includes containment, eradication, and post‑incident review.

## 9. Policy Governance
- **Policy Owner:** IT Security Department  
- **Effective Date:** 2024‑09‑30  
- **Last Updated:** [Insert Date]  
- **Review Cycle:** Annually, or sooner if regulatory or business changes occur.