            email_sender = 'alerts4vbalpha@gmail.com'
            email_password = 'yqhw llcy ttlv pdin'
            email_receiver = 'sahilnalemail@gmail.com'
            subject = f'Thanks for registering'

            body = "This is working"
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject
            em.set_content(body)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())