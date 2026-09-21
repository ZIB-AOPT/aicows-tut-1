#include "bot.hpp"
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/ssl/host_name_verification.hpp>
#include <boost/beast/core.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/beast/websocket.hpp>
#include <boost/beast/websocket/ssl.hpp>
#include <openssl/ssl.h>
#include <cstdlib>
#include <iostream>
#include <regex>
#include <stdexcept>
#include <string>

namespace net = boost::asio;
namespace ssl = net::ssl;
namespace beast = boost::beast;
namespace websocket = beast::websocket;
using tcp = net::ip::tcp;
constexpr const char* protocol = "hidden-gems-2.0";

struct Options {
    std::string server = "http://127.0.0.1:8765";
    std::string match;
    std::string name = "C++ template";
};

struct Origin {
    bool tls;
    std::string host, authority, port;
};

Origin parse_origin(std::string server) {
    while (!server.empty() && server.back() == '/') server.pop_back();
    // Origins only; brackets are required for IPv6 literals. No credentials,
    // path, query or fragment can be smuggled into the authenticated handshake.
    const std::regex pattern(R"(^(http|https|ws|wss)://(\[[0-9a-fA-F:]+\]|[a-zA-Z0-9.-]+)(:([0-9]+))?$)");
    std::smatch parts;
    if (!std::regex_match(server, parts, pattern)) {
        throw std::runtime_error("Use a server origin such as http://127.0.0.1:8765 (no path or query)");
    }
    const bool tls = parts[1] == "https" || parts[1] == "wss";
    const std::string authority = parts[2].str() + parts[3].str();
    std::string host = parts[2];
    if (host.front() == '[') host = host.substr(1, host.size() - 2);
    const auto port = parts[4].matched ? parts[4].str() : (tls ? "443" : "80");
    const auto number = std::stoul(port);
    if (number == 0 || number > 65535) throw std::runtime_error("Invalid server port");
    return {tls, host, authority, port};
}

template <typename Stream>
void play(Stream& socket, const Options& options, const Origin& origin, const std::string& token) {
    socket.read_message_max(1 << 20);
    socket.set_option(websocket::stream_base::decorator([&token](websocket::request_type& request) {
        request.set(beast::http::field::authorization, "Bearer " + token);
    }));
    socket.handshake(origin.authority, "/ws/bot/" + options.match);
    socket.text(true);
    const auto send = [&socket](const Json& value) {
        const auto text = value.dump();
        socket.write(net::buffer(text));
    };
    send({{"type", "hello"}, {"protocol", protocol}, {"name", options.name}});
    MyBot bot;
    bool initialized = false;
    for (;;) {
        beast::flat_buffer buffer;
        // Beast handles ping/pong and fragmented frames while reading.
        socket.read(buffer);
        if (!socket.got_text()) throw std::runtime_error("Expected a text JSON message");
        const auto message = Json::parse(beast::buffers_to_string(buffer.data()));
        const auto type = message.at("type").get<std::string>();
        if (!initialized && type != "init") throw std::runtime_error("Expected init before game messages");
        if (type == "init") {
            if (initialized || message.at("protocol") != protocol) {
                throw std::runtime_error("Unexpected init or incompatible protocol");
            }
            bot.initialize(message);
            initialized = true;
            std::cerr << "Connected. Waiting for the operator to start the match.\n";
        } else if (type == "turn") {
            send({{"type", "scan"}, {"turn", message.at("turn")}, {"n", bot.choose_scan(message)}});
        } else if (type == "observation") {
            const auto action = bot.choose_move(message);
            send({{"type", "move"}, {"turn", message.at("turn")},
                  {"direction", action.at("direction")}, {"distance", action.at("distance")}});
        } else if (type == "result") {
            std::cout << message.dump() << std::endl;
            beast::error_code ignored;
            socket.close(websocket::close_code::normal, ignored);
            return;
        } else {
            throw std::runtime_error("Unknown game message type");
        }
    }
}

int main(int argc, char** argv) {
    try {
        Options options;
        for (int i = 1; i < argc; ++i) {
            const std::string option = argv[i];
            if (option == "--help" || option == "-h") {
                std::cout << "Usage: hiddengems-bot --match MATCH_ID [--server http://127.0.0.1:8765] [--name NAME]\n"
                             "Set HIDDENGEMS_BOT_TOKEN to this slot's credential.\n";
                return 0;
            }
            if (option != "--server" && option != "--match" && option != "--name") {
                throw std::runtime_error("Unknown argument; use --help");
            }
            if (++i == argc) throw std::runtime_error("Missing option value");
            if (option == "--server") options.server = argv[i];
            if (option == "--match") options.match = argv[i];
            if (option == "--name") options.name = argv[i];
        }
        if (!std::regex_match(options.match, std::regex("[0-9a-fA-F]{16}"))) {
            throw std::runtime_error("--match must be the server's 16-character hexadecimal match ID");
        }
        const char* credential = std::getenv("HIDDENGEMS_BOT_TOKEN");
        if (!credential || !*credential) throw std::runtime_error("Set HIDDENGEMS_BOT_TOKEN to this slot's credential");
        const std::string token = credential;
        if (token.find_first_of("\r\n") != std::string::npos) throw std::runtime_error("Invalid token characters");
        const auto origin = parse_origin(options.server);
        net::io_context context;
        tcp::resolver resolver(context);
        const auto endpoints = resolver.resolve(origin.host, origin.port);
        if (origin.tls) {
            ssl::context tls(ssl::context::tls_client);
            tls.set_default_verify_paths();
            tls.set_verify_mode(ssl::verify_peer);
            websocket::stream<beast::ssl_stream<tcp::socket>> socket(context, tls);
            socket.next_layer().set_verify_callback(ssl::host_name_verification(origin.host));
            if (!SSL_set_tlsext_host_name(socket.next_layer().native_handle(), origin.host.c_str())) {
                throw std::runtime_error("Could not set the TLS server name");
            }
            net::connect(beast::get_lowest_layer(socket), endpoints);
            beast::get_lowest_layer(socket).set_option(tcp::no_delay(true));
            socket.next_layer().handshake(ssl::stream_base::client);
            play(socket, options, origin, token);
        } else {
            websocket::stream<tcp::socket> socket(context);
            net::connect(socket.next_layer(), endpoints);
            socket.next_layer().set_option(tcp::no_delay(true));
            play(socket, options, origin, token);
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Bot error: " << error.what() << '\n';
        return 1;
    }
}
