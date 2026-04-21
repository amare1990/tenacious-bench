def generate_email(company, signals, ai, gap):
    subject = f"{company.company_name} – quick observation"

    body = f"""
Hi,

I noticed that {signals.funding_signal} and {signals.hiring_velocity_signal}.

Teams at this stage often run into bottlenecks scaling engineering capacity.

Interestingly, companies like {", ".join(gap.peer_group)} are already investing in {", ".join(gap.top_quartile_practices)}, while it looks like {company.company_name} may not yet be doing this.

Would it be useful to compare notes for 30 minutes?

Best,
Tenacious
"""

    return {
        "subject": subject.strip(),
        "body": body.strip()
    }
