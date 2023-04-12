import email


def get_email_body(email_string):
    email_parser = email.parser.Parser()
    parsed_string = email_parser.parsestr(email_string)

    def _get_body(emailobj):
        if emailobj.is_multipart():
            for payload in emailobj.get_payload():
                if payload.is_multipart():
                    return _get_body(payload)

                body = payload.get_payload()
                if payload.get_content_type() == "text/plain":
                    return body
        else:
            return emailobj.get_payload()

    return _get_body(parsed_string)
