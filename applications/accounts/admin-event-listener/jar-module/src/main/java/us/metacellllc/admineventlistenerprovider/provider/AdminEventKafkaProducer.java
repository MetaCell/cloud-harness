package us.metacellllc.admineventlistenerprovider.provider;

import java.util.Properties;
import java.util.ArrayList;
import java.util.List;

import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;

public class AdminEventKafkaProducer {

   private String topicName = "keycloak.fct.admin";
   private Properties props = new Properties();;

   public AdminEventKafkaProducer() {
      //Assign localhost id
      props.put("bootstrap.servers", "kafka-0.broker:9092");
      
      //Set acknowledgements for producer requests.      
      props.put("acks", "all");
      
      //If the request fails, the producer can automatically retry,
      props.put("retries", 0);
      
      //Specify buffer size in config
      props.put("batch.size", 16384);
      
      //Reduce the no of requests less than 0   
      props.put("linger.ms", 1);
      
      //The buffer.memory controls the total amount of memory available to the producer for buffering.   
      props.put("buffer.memory", 33554432);
      
      props.put("value.serializer","org.apache.kafka.common.serialization.StringSerializer");
      props.put("key.serializer","org.apache.kafka.common.serialization.StringSerializer");
   }
 
   public void SendMessage(String resourceType, String operationType, String resourcePath) throws Exception{
      // workaround for jvm not discovering the kafka serializer classes
      Thread.currentThread().setContextClassLoader(null);

      Producer<String, String> producer = new KafkaProducer
         <String, String>(props);
    
      String key = resourcePath;
      StringBuilder sbValue = new StringBuilder();
      sbValue.append("{");
      sbValue.append("\"resource-type\": \""+resourceType+"\",");
      sbValue.append("\"operation-type\": \""+operationType+"\",");
      sbValue.append("\"resource-path\": \""+resourcePath+"\"");
      sbValue.append("}");
      System.out.println("Sending message "+sbValue.toString());
      producer.send(new ProducerRecord<String, String>(topicName, 
         resourceType, sbValue.toString()));
      System.out.println("Message sent successfully");
      producer.close();
   }
}