from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    text = [
        "Code de Commerce Marocain - Extraits pour test RAG",
        "",
        "Article 1 : La présente loi régit les actes de commerce et les commerçants.",
        "Article 2 : Sont des actes de commerce par nature :",
        "- L'achat de meubles ou d'immeubles pour les revendre.",
        "- Les opérations de banque, de change et de courtage.",
        "- L'exploitation de mines, de carrières et de sources.",
        "",
        "L'immatriculation au registre du commerce est obligatoire pour tout commerçant.",
        "Le registre du commerce est composé de registres locaux et d'un registre central.",
        "Tout commerçant doit tenir une comptabilité conformément à la loi.",
        "",
        "Livre II : Le Fonds de Commerce",
        "Le fonds de commerce comprend obligatoirement la clientèle et l'achandage.",
        "Il comprend aussi tous autres biens nécessaires à l'exploitation du fonds,",
        "tels que l'enseigne, le nom commercial, le droit au bail, le mobilier commercial,",
        "le matériel et l'outillage, les brevets d'invention, les licences, les marques de fabrique.",
    ]
    
    y = height - 50
    for line in text:
        c.drawString(50, y, line)
        y -= 20
        
    c.save()

if __name__ == "__main__":
    doc_path = r"C:\Users\laani\Desktop\AI_Legal_Assistant_Maroc\documents\code_commerce_test.pdf"
    create_pdf(doc_path)
    print(f"✅ Fichier PDF créé : {doc_path}")
