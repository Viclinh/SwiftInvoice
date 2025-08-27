## Inspiration
SwiftInvoice is a simple yet powerful invoicing platform built for small businesses, freelancers, and e-commerce sellers who don’t have time to wrestle with complicated accounting tools. With SwiftInvoice, you can create and send professional, branded invoices in just one click—saving you hours of manual formatting so you can focus on running your business.

## What it does
SwiftInvoice lets users quickly create, merge, and split professional invoices. You can upload invoices data, generate branded invoices with one click, download or delete them, and even merge or split invoice PDFs as needed.

## How we built it
We used Foxit Document Generation API to create invoices from uploaded data and templates. For advanced PDF handling, such as merging or splitting invoices, we integrated the Foxit PDF Editor API. The front end allows users to upload data files, manage invoices, and download the final PDFs.

## Challenges we ran into
- Designing an interface that stayed simple but still powerful.
- Handling different invoice data formats.
- Making sure merged and split PDFs looked consistent and professional.
- Managing file uploads and downloads seamlessly.

## Accomplishments that we're proud of
- Built a full invoicing system from data upload to PDF generation.
- Integrated multiple Foxit APIs into a smooth workflow.
- Created a user-friendly tool that saves time and frustration for small businesses.

##What we learned
- How to leverage Foxit document generation APIs effectively.
- We learnt to write code to edit PDF using Foxit PDF API

##What's next for SwiftInvoice
- Add subscription plans with more templates and advanced features.
- Support recurring invoices and automatic email delivery.
- Build integrations with payment platforms (Stripe, PayPal).
