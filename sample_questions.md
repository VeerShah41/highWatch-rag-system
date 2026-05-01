# HighWatch AI RAG System - Evaluation Details

## Resources

*   **Sample Dataset:** `demo_docs/company_refund_policy.txt` (Highwatch AI — Company Refund and Returns Policy)
*   **Sample Folder Link:** [Google Drive Demo Folder](https://drive.google.com/drive/folders/1ZP8lXDro7XL3Kfyg2avmDwlSOcAgabc-?usp=sharing)

---

## Evaluation Questions based on Dataset

Here are the questions categorized by difficulty level that can be used to test the RAG system's responses based on the provided refund policy document.

### Level: Easy (Direct Extraction)
These questions test the system's ability to extract explicit facts directly from the document.

1.  **Question:** Within how many days of the purchase date must a refund request be submitted?
    *   **Expected Answer:** Within 30 days of the purchase date.

2.  **Question:** What is the support email address for submitting a refund request?
    *   **Expected Answer:** support@highwatch.ai

3.  **Question:** Can I get a refund for an annual subscription plan after 20 days?
    *   **Expected Answer:** No, annual subscription plans are not eligible for refunds after 14 days of activation.

### Level: Medium (Contextual Understanding & Multi-step)
These questions require the system to combine multiple pieces of information or understand specific conditions.

4.  **Question:** What is the complete procedure for reporting a defective product?
    *   **Expected Answer:** The issue must be reported within 7 days of receiving the product. Photo or video evidence must be submitted via email to support@highwatch.ai with the specific subject line: "Damaged Item - Order #[ORDER_ID]". Upon verification, a refund/replacement is issued in 5-7 business days.

5.  **Question:** Under what circumstances can a customer receive a partial refund?
    *   **Expected Answer:** Partial refunds are issued in three cases: (1) A monthly subscription is cancelled mid-cycle (prorated refund), (2) Service was partially delivered due to Highwatch's technical issues, or (3) For promotional items where only part of the order is returned.

### Level: Hard (Reasoning & Escalation Workflows)
These questions test the system's ability to understand workflows, exceptions, and synthesize a comprehensive answer.

6.  **Question:** A customer whose refund request was rejected last week is extremely unhappy and wants to dispute the decision. Explain the exact steps they need to take and how long they will have to wait for a final resolution.
    *   **Expected Answer:** The customer needs to escalate the dispute by emailing refund-escalation@highwatch.ai. A senior team member will review the escalation within 3 business days, and the final decision will then be communicated to the customer in writing.

7.  **Question:** A client purchased API credits and used half of them before deciding the service wasn't a good fit. They are requesting a refund for the unused half within the 30-day window. Are they eligible according to the policy?
    *   **Expected Answer:** Yes, they are likely eligible for the unused half. The policy states that API credits that "have been consumed" are non-refundable, but implies unused credits may be refundable. Additionally, the policy allows partial refunds when a product or service has "not been fully used or consumed," provided it is within the 30-day window.
