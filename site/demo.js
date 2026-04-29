const lines = [
    { text: "━━━ PASSO 1/6: Fluxo Feliz ━━━", cls: "cyan bold", delay: 400 },
    { text: "", delay: 200 },
    { text: "📤 Enviando mensagem para API Gateway...", cls: "cyan", delay: 600 },
    { text: '  URL: https://hmpsvwpjz5.execute-api.us-east-1.amazonaws.com/dev/send', cls: "dim", delay: 300 },
    { text: '  ✅ Mensagem enviada!', cls: "green", delay: 500 },
    { text: '  message_id: d6ab2ffc-d522-4a5a-ae5b-18aa263ee7f0', cls: "dim", delay: 200 },
    { text: '  request_id: 2b8a5848-e35e-41c1-a7e4-4df26dc22a96', cls: "dim", delay: 200 },
    { text: "", delay: 300 },
    { text: "⏳ Aguardando Consumer processar...", cls: "yellow", delay: 1500 },
    { text: '  ✅ Item gravado no DynamoDB!', cls: "green", delay: 500 },
    { text: '  status: processed', cls: "dim", delay: 200 },
    { text: "", delay: 600 },

    { text: "━━━ PASSO 2/6: Injetando Erro ━━━", cls: "cyan bold", delay: 400 },
    { text: "", delay: 200 },
    { text: "🔴 Removendo permissão dynamodb:PutItem do Consumer...", cls: "red", delay: 800 },
    { text: "  Simulando erro de IAM que acontece em produção", cls: "dim", delay: 300 },
    { text: "  ✅ Permissão removida!", cls: "green", delay: 500 },
    { text: "", delay: 300 },
    { text: "⏳ Aguardando propagação da IAM policy...", cls: "yellow", delay: 1200 },
    { text: "", delay: 600 },

    { text: "━━━ PASSO 3/6: Mensagem com Erro ━━━", cls: "cyan bold", delay: 400 },
    { text: "", delay: 200 },
    { text: "📤 Enviando mensagem (vai falhar no Consumer)...", cls: "cyan", delay: 600 },
    { text: '  ✅ Producer enviou para SQS (ele não sabe que vai falhar)', cls: "green", delay: 500 },
    { text: '  request_id: 415c63a5-a9df-4bbf-8ca1-a4c1ed6f4581', cls: "dim", delay: 200 },
    { text: "", delay: 300 },
    { text: "⏳ Aguardando Consumer falhar...", cls: "yellow", delay: 1500 },
    { text: "", delay: 600 },

    { text: "━━━ PASSO 4/6: Diagnóstico com MCP Server ━━━", cls: "cyan bold", delay: 400 },
    { text: "", delay: 200 },
    { text: "🔍 Tool 1/3: search_logs (CloudWatch)...", cls: "magenta", delay: 800 },
    { text: '  ❌ [ERROR] AccessDeniedException - User: troubleshooter-dev-consumer-role', cls: "red", delay: 400 },
    { text: '     is not authorized to perform: dynamodb:PutItem', cls: "red", delay: 300 },
    { text: '     on resource: troubleshooter-dev-table', cls: "red", delay: 300 },
    { text: "", delay: 400 },
    { text: "🔍 Tool 2/3: search_trace (X-Ray)...", cls: "magenta", delay: 800 },
    { text: '  ConsumerFunction → ERROR → AccessDeniedException', cls: "dim", delay: 400 },
    { text: "", delay: 400 },
    { text: "🔍 Tool 3/3: search_lambda_config...", cls: "magenta", delay: 800 },
    { text: '  function: troubleshooter-dev-ConsumerFunction', cls: "dim", delay: 200 },
    { text: '  role: troubleshooter-dev-consumer-role', cls: "dim", delay: 200 },
    { text: '  timeout: 30s | memory: 128MB | runtime: python3.11', cls: "dim", delay: 200 },
    { text: "", delay: 500 },
    { text: "🎯 DIAGNÓSTICO COMPLETO", cls: "red bold", delay: 600 },
    { text: "", delay: 200 },
    { text: '  Causa: IAM Role sem permissão dynamodb:PutItem', cls: "yellow", delay: 400 },
    { text: '  Correção: {"Effect":"Allow","Action":["dynamodb:PutItem"],', cls: "cyan", delay: 300 },
    { text: '   "Resource":"arn:aws:dynamodb:us-east-1:*:table/troubleshooter-dev-table"}', cls: "cyan", delay: 300 },
    { text: "", delay: 600 },

    { text: "━━━ PASSO 5/6: Aplicando Correção ━━━", cls: "cyan bold", delay: 400 },
    { text: "", delay: 200 },
    { text: "🔧 Restaurando permissão dynamodb:PutItem...", cls: "green", delay: 800 },
    { text: "  ✅ Permissão restaurada!", cls: "green", delay: 500 },
    { text: "", delay: 300 },
    { text: "⏳ Aguardando propagação...", cls: "yellow", delay: 1200 },
    { text: "", delay: 600 },

    { text: "━━━ PASSO 6/6: Validando Correção ━━━", cls: "cyan bold", delay: 400 },
    { text: "", delay: 200 },
    { text: "📤 Enviando mensagem novamente...", cls: "cyan", delay: 600 },
    { text: "  ✅ Mensagem enviada!", cls: "green", delay: 500 },
    { text: "", delay: 300 },
    { text: "⏳ Aguardando Consumer processar...", cls: "yellow", delay: 1500 },
    { text: "  ✅ Item gravado no DynamoDB!", cls: "green", delay: 500 },
    { text: "  status: processed", cls: "dim", delay: 200 },
    { text: "", delay: 600 },

    { text: "╔══════════════════════════════════════════╗", cls: "green bold", delay: 200 },
    { text: "║          🎉 DEMO COMPLETA!               ║", cls: "green bold", delay: 200 },
    { text: "╠══════════════════════════════════════════╣", cls: "green bold", delay: 200 },
    { text: "║  ✅ Fluxo feliz: POST → SQS → DynamoDB  ║", cls: "green bold", delay: 200 },
    { text: "║  ✅ Erro injetado: AccessDeniedException ║", cls: "green bold", delay: 200 },
    { text: "║  ✅ Diagnóstico: 3 tools MCP em ~3s      ║", cls: "green bold", delay: 200 },
    { text: "║  ✅ Correção: IAM policy restaurada      ║", cls: "green bold", delay: 200 },
    { text: "║  ✅ Validação: Fluxo OK novamente        ║", cls: "green bold", delay: 200 },
    { text: "╚══════════════════════════════════════════╝", cls: "green bold", delay: 200 },
];

let running = false;

function startDemo() {
    if (running) return;
    running = true;
    document.getElementById("btn-play").style.display = "none";
    document.getElementById("btn-reset").style.display = "inline-block";

    const output = document.getElementById("terminal-output");
    output.innerHTML = '<div class="term-line dim">$ python run.py --auto</div><div class="term-line"></div>';

    let i = 0;
    function next() {
        if (i >= lines.length) { running = false; return; }
        const line = lines[i++];
        const div = document.createElement("div");
        div.className = "term-line " + (line.cls || "");
        div.textContent = line.text;
        output.appendChild(div);
        output.scrollTop = output.scrollHeight;
        setTimeout(next, line.delay || 300);
    }
    setTimeout(next, 500);
}

function resetDemo() {
    running = false;
    const output = document.getElementById("terminal-output");
    output.innerHTML = '<div class="term-line dim">$ python run.py --auto</div><div class="term-line"></div>';
    document.getElementById("btn-play").style.display = "inline-block";
    document.getElementById("btn-reset").style.display = "none";
}
