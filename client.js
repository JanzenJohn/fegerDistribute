const WebSocket = require("ws");
const argparse = require("argparse");

const argparser = argparse.ArgumentParser({})
argparser.add_argument("--master-host", { default: "127.0.0.1" })
argparser.add_argument("--master-port", { default: "8765" })
argparser.add_argument("--master-ssl", { default: false })
argparser.add_argument("--sd-host", { default: "127.0.0.1" })
argparser.add_argument("--sd-port", { default: "7860" })
argparser.add_argument("--sd-ssl", { default: false })

const args = argparser.parse_args()

let master_url = args.master_ssl ? "wss://" : "ws://"
master_url += args.master_host + ":" + args.master_port
let sd_url = args.sd_ssl ? "https://" : "http://"
sd_url += args.sd_host + ":" + args.sd_port
let retires = 0

function create() {
    console.log("TRYING TO CONNECT")
    x = new WebSocket(master_url);

    x.onerror = function () {
        console.log("ERROR WHILE CONNECTING")
    }
    x.onclose = function () {
        retires += 1
        if (retires < 30) {
            setTimeout(create, 5000)
        } else {
            console.log("giving up")
            process.exit(1)
        }
    }
    x.onmessage = async function (msg) {
        let [id, data] = msg.data.split("::")
        console.log({ id, data })
        const resp = await fetch(sd_url + "/sdapi/v1/txt2img", { body: JSON.stringify({ prompt: data }), method: "POST", headers: { "Content-Type": "application/json" } })
        console.log("got resp")
        if (resp.status == 200) {
            console.log("went good")
            await x.send("DONE_JOB::" + id + "::" + JSON.parse(await resp.text())["images"][0])
        } else {
            console.log(`wend bad ` + resp.status)
            await x.send("ERROR_JOB::" + id + "::" + "idk")
        }
        await x.send("NEED_JOB")

    }

    x.onopen = function () {
        console.log("connected")
        x.send("NEED_JOB")
        retires = 0
    }
}


create()