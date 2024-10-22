$(document).ready(function () {
    let socket;
    let totalEmails = 0;
    let processedEmails = 0;

    // Update progress information at the top of the page
    function updateProgressInfo() {
        $('#progress-info').text(`Processed: ${processedEmails} / ${totalEmails} emails`);
    }

    // Update the progress bar
    function updateProgressBar(progress) {
        $('#progress-bar').css('width', progress + '%').text(progress + '%').attr('aria-valuenow', progress);
    }

    // Add email to the table
    function addEmailToTable(email) {
        let attachments = '';
        if (email.attachments) {
            email.attachments.forEach(att => {
                attachments += `<a href="${att.url}" target="_blank">${att.filename}</a><br>`;
            });
        }

        const row = `
                <tr>
                    <td>${email.subject}</td>
                    <td>${email.from_address}</td>
                    <td>${email.sent_at}</td>
                    <td>${email.received_at}</td>
                    <td>${attachments}</td>
                    <td>${email.body.substring(0, 50)}...</td>
                </tr>`;
        $('#email-table tbody').append(row);
    }

    // Fetch already processed emails on page load
    function loadProcessedEmails() {
        $.getJSON('/api/processed_emails/', function (data) {
            data.emails.forEach(email => {
                addEmailToTable(email);
            });
            totalEmails = data.total_emails || 0;
            processedEmails = data.processed_emails || 0;
            updateProgressInfo();
        });
    }

    // Call function to load already processed emails when page loads
    loadProcessedEmails();

    $('#fetch-mails').click(function () {
        $(this).prop('disabled', true);
        processedEmails = 0;
        totalEmails = 0;
        updateProgressInfo();
        updateProgressBar(0);

        // Open WebSocket connection
        socket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/emails/');

        socket.onmessage = function (e) {
            const data = JSON.parse(e.data);

            if (data.total_emails !== undefined) {
                totalEmails = data.total_emails;
            }
            if (data.processed_emails !== undefined) {
                processedEmails = data.processed_emails;
                const progress = Math.min((processedEmails / totalEmails) * 100, 100);
                updateProgressInfo();
                updateProgressBar(progress);
            }

            if (data.email) {
                addEmailToTable(data.email);
            }

            if (data.status === 'complete') {
                $('#fetch-mails').prop('disabled', false);
                updateProgressBar(100);
            }
        };

        socket.onopen = () => socket.send(JSON.stringify({'action': 'start_fetching'}));
        socket.onclose = () => $('#fetch-mails').prop('disabled', false);
    });
});