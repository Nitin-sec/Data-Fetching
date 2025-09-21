package org.telegram.fetcher;

import org.drinkless.tdlib.Client;
import org.drinkless.tdlib.TdApi;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class data_fetcher_test {
    private static Client client = null;
    private static boolean haveAuthorization = false;
    private static boolean needQuit = false;

    private static final Lock authorizationLock = new ReentrantLock();
    private static final Condition gotAuthorization = authorizationLock.newCondition();

    private static final int API_ID = 12345678; // Replace with your actual API ID
    private static final String API_HASH = "your_api_hash_here"; // Replace with your actual API Hash
    private static final String PHONE_NUMBER = "+1234567890"; // Replace with your actual phone number

    private static final ConcurrentHashMap<Long, TdApi.Chat> chats = new ConcurrentHashMap<>();

    private static void print(String str) {
        System.out.println(str);
    }

    private static class AuthorizationRequestHandler implements Client.ResultHandler {
        @Override
        public void onResult(TdApi.Object object) {
            switch (object.getConstructor()) {
                case TdApi.Error.CONSTRUCTOR:
                    print("Error: " + object);
                    break;
                case TdApi.Ok.CONSTRUCTOR:
                    break;
                default:
                    print("Unexpected response: " + object);
            }
        }
    }

    private static void onAuthorizationStateUpdated(TdApi.AuthorizationState authorizationState) {
        if (authorizationState != null) {
            switch (authorizationState.getConstructor()) {
                case TdApi.AuthorizationStateWaitTdlibParameters.CONSTRUCTOR: {
                    TdApi.TdlibParameters parameters = new TdApi.TdlibParameters();
                    parameters.databaseDirectory = "tdlib";
                    parameters.useMessageDatabase = true;
                    parameters.useSecretChats = true;
                    parameters.apiId = API_ID;
                    parameters.apiHash = API_HASH;
                    parameters.systemLanguageCode = "en";
                    parameters.deviceModel = "Desktop";
                    parameters.applicationVersion = "1.0";
                    parameters.enableStorageOptimizer = true;

                    client.send(new TdApi.SetTdlibParameters(parameters), new AuthorizationRequestHandler());
                    break;
                }
                case TdApi.AuthorizationStateWaitEncryptionKey.CONSTRUCTOR: {
                    client.send(new TdApi.CheckDatabaseEncryptionKey(), new AuthorizationRequestHandler());
                    break;
                }
                case TdApi.AuthorizationStateWaitPhoneNumber.CONSTRUCTOR: {
                    client.send(new TdApi.SetAuthenticationPhoneNumber(PHONE_NUMBER, null), new AuthorizationRequestHandler());
                    break;
                }
                case TdApi.AuthorizationStateWaitCode.CONSTRUCTOR: {
                    Scanner scanner = new Scanner(System.in);
                    print("Enter verification code: ");
                    String code = scanner.nextLine();
                    client.send(new TdApi.CheckAuthenticationCode(code), new AuthorizationRequestHandler());
                    break;
                }
                case TdApi.AuthorizationStateWaitPassword.CONSTRUCTOR: {
                    Scanner scanner = new Scanner(System.in);
                    print("Enter 2FA password: ");
                    String password = scanner.nextLine();
                    client.send(new TdApi.CheckAuthenticationPassword(password), new AuthorizationRequestHandler());
                    break;
                }
                case TdApi.AuthorizationStateReady.CONSTRUCTOR: {
                    haveAuthorization = true;
                    authorizationLock.lock();
                    try {
                        gotAuthorization.signal();
                    } finally {
                        authorizationLock.unlock();
                    }
                    break;
                }
                default:
                    print("Unsupported authorization state: " + authorizationState);
            }
        }
    }

    private static class UpdateHandler implements Client.ResultHandler {
        @Override
        public void onResult(TdApi.Object object) {
            switch (object.getConstructor()) {
                case TdApi.UpdateAuthorizationState.CONSTRUCTOR:
                    onAuthorizationStateUpdated(((TdApi.UpdateAuthorizationState) object).authorizationState);
                    break;
                case TdApi.UpdateNewChat.CONSTRUCTOR: {
                    TdApi.UpdateNewChat updateNewChat = (TdApi.UpdateNewChat) object;
                    chats.put(updateNewChat.chat.id, updateNewChat.chat);
                    break;
                }
                case TdApi.UpdateChatTitle.CONSTRUCTOR: {
                    TdApi.UpdateChatTitle updateChat = (TdApi.UpdateChatTitle) object;
                    TdApi.Chat chat = chats.get(updateChat.chatId);
                    if (chat != null) {
                        synchronized (chat) {
                            chat.title = updateChat.title;
                        }
                    }
                    break;
                }
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        print("Telegram Group Data Fetcher (Java TDLib)");
        print("==========================================");

        // Create client
        client = Client.create(new UpdateHandler(), null, null);

        // Wait for authorization
        authorizationLock.lock();
        try {
            while (!haveAuthorization) {
                gotAuthorization.await();
            }
        } finally {
            authorizationLock.unlock();
        }

        print("Successfully connected to Telegram!");

        // Load chats
        loadChats();

        // Get group names from user
        Scanner scanner = new Scanner(System.in);
        List<String> groupNames = new ArrayList<>();
        
        print("\n=== Group Names ===");
        print("Enter the names of the groups you want to fetch data from.");
        print("Type 'done' when you're finished adding groups.");
        
        while (true) {
            System.out.print("Group " + (groupNames.size() + 1) + " name (or 'done' to finish): ");
            String groupName = scanner.nextLine().trim();
            if ("done".equalsIgnoreCase(groupName)) {
                break;
            }
            if (!groupName.isEmpty()) {
                groupNames.add(groupName);
                print("Added: " + groupName);
            }
        }

        if (groupNames.isEmpty()) {
            print("Error: You must specify at least one group!");
            return;
        }

        // Calculate time limit (6 hours ago)
        long timeLimit = Instant.now().minusSeconds(6 * 3600).getEpochSecond();
        print("\nFetching messages newer than: " + 
              LocalDateTime.ofEpochSecond(timeLimit, 0, ZoneOffset.UTC));

        List<MessageInfo> allMessages = new ArrayList<>();

        // Process each group
        for (String groupName : groupNames) {
            print("\nSearching for group: '" + groupName + "'...");
            
            TdApi.Chat targetChat = findChatByName(groupName);
            if (targetChat == null) {
                print("Group '" + groupName + "' not found! Make sure you're a member of this group.");
                continue;
            }

            print("Found group: " + targetChat.title);
            
            // Fetch messages from group
            List<MessageInfo> messages = fetchMessagesFromChat(targetChat.id, groupName, timeLimit);
            allMessages.addAll(messages);
        }

        // Sort messages by date (newest first)
        allMessages.sort((a, b) -> Long.compare(b.date, a.date));

        // Display results
        print("\n" + "=".repeat(80));
        print("SUMMARY");
        print("=".repeat(80));
        print("Total messages found: " + allMessages.size());
        print("Time range: Last 6 hours from " + LocalDateTime.now());
        print("Groups processed: " + groupNames.size());

        if (!allMessages.isEmpty()) {
            print("\n" + "=".repeat(80));
            print("MESSAGES");
            print("=".repeat(80));
            
            for (MessageInfo message : allMessages) {
                printMessage(message);
                print(""); // Empty line
            }
        } else {
            print("\nNo messages found in the specified time range.");
        }

        // Close client
        client.send(new TdApi.Close(), object -> {});
    }

    private static void loadChats() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(1);
        
        client.send(new TdApi.LoadChats(null, 100), new Client.ResultHandler() {
            @Override
            public void onResult(TdApi.Object object) {
                latch.countDown();
            }
        });
        
        latch.await();
        Thread.sleep(1000); // Wait for chats to load
    }

    private static TdApi.Chat findChatByName(String name) {
        for (TdApi.Chat chat : chats.values()) {
            if (chat.title.toLowerCase().contains(name.toLowerCase())) {
                return chat;
            }
        }
        return null;
    }

    private static List<MessageInfo> fetchMessagesFromChat(long chatId, String groupName, long timeLimit) {
        List<MessageInfo> messages = new ArrayList<>();
        print("\nFetching messages from '" + groupName + "'...");

        CountDownLatch latch = new CountDownLatch(1);
        
        client.send(new TdApi.GetChatHistory(chatId, 0, 0, 100, false), new Client.ResultHandler() {
            @Override
            public void onResult(TdApi.Object object) {
                if (object instanceof TdApi.Messages) {
                    TdApi.Messages messagesResult = (TdApi.Messages) object;
                    
                    for (TdApi.Message message : messagesResult.messages) {
                        if (message.date < timeLimit) {
                            break;
                        }
                        
                        MessageInfo msgInfo = new MessageInfo();
                        msgInfo.id = message.id;
                        msgInfo.date = message.date;
                        msgInfo.senderId = getSenderId(message.senderId);
                        msgInfo.text = getMessageText(message);
                        msgInfo.hasMedia = !(message.content instanceof TdApi.MessageText);
                        msgInfo.groupName = groupName;
                        
                        messages.add(msgInfo);
                    }
                }
                latch.countDown();
            }
        });

        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        print("Found " + messages.size() + " messages in '" + groupName + "' from the last 6 hours");
        return messages;
    }

    private static String getMessageText(TdApi.Message message) {
        if (message.content instanceof TdApi.MessageText) {
            return ((TdApi.MessageText) message.content).text.text;
        }
        return "[Non-text message]";
    }

    private static long getSenderId(TdApi.MessageSender sender) {
        if (sender instanceof TdApi.MessageSenderUser) {
            return ((TdApi.MessageSenderUser) sender).userId;
        } else if (sender instanceof TdApi.MessageSenderChat) {
            return ((TdApi.MessageSenderChat) sender).chatId;
        }
        return 0;
    }

    private static void printMessage(MessageInfo message) {
        print("================================================================================");
        print("GROUP: " + message.groupName);
        print("MESSAGE ID: " + message.id);
        print("DATE: " + LocalDateTime.ofEpochSecond(message.date, 0, ZoneOffset.UTC) + " UTC");
        print("SENDER ID: " + message.senderId);
        
        if (message.hasMedia) {
            print("MEDIA: Yes");
        }
        
        print("MESSAGE:");
        if (message.text != null && !message.text.isEmpty()) {
            String[] lines = message.text.split("\n");
            for (String line : lines) {
                if (line.length() > 120) {
                    while (line.length() > 120) {
                        print("  " + line.substring(0, 120));
                        line = line.substring(120);
                    }
                    if (!line.isEmpty()) {
                        print("  " + line);
                    }
                } else {
                    print("  " + line);
                }
            }
        } else {
            print("  [No text content]");
        }
    }

    private static class MessageInfo {
        long id;
        long date;
        long senderId;
        String text;
        boolean hasMedia;
        String groupName;
    }
}