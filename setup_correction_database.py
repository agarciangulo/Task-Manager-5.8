#!/usr/bin/env python3
"""
Setup script for correction handler database tables.
This will create the necessary tables in your Google Cloud PostgreSQL database.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_correction_database():
    """Set up the correction handler database tables."""
    print("🔧 Setting up Correction Handler Database...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set. Please set it first:")
        print("   export DATABASE_URL='postgresql://postgres:S2uwupRe@34.58.40.214:5432/email_archive'")
        return False
    
    print(f"✅ Using database: {database_url[:30]}...")
    
    try:
        # Import the correction models
        from src.core.models.correction_models import Base, TaskCorrectionLog, TaskCorrection
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        
        print("✅ Imported correction models")
        
        # Create engine
        engine = create_engine(database_url)
        print("✅ Created database engine")
        
        # Test connection
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT version();")
                version = result.fetchone()[0]
                print(f"✅ Database connection successful")
                print(f"   PostgreSQL version: {version}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Create tables
        print("\n📋 Creating correction handler tables...")
        Base.metadata.create_all(engine)
        print("✅ Created all correction handler tables")
        
        # Verify tables exist
        print("\n📋 Verifying tables...")
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('task_correction_logs', 'task_corrections')
                ORDER BY table_name;
            """)
            tables = [row[0] for row in result.fetchall()]
            
            if 'task_correction_logs' in tables:
                print("✅ task_correction_logs table exists")
            else:
                print("❌ task_correction_logs table not found")
                
            if 'task_corrections' in tables:
                print("✅ task_corrections table exists")
            else:
                print("❌ task_corrections table not found")
        
        # Test table structure
        print("\n📋 Testing table structure...")
        with engine.connect() as conn:
            # Check task_correction_logs columns
            result = conn.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'task_correction_logs'
                ORDER BY ordinal_position;
            """)
            columns = result.fetchall()
            print("📋 task_correction_logs columns:")
            for col_name, data_type in columns:
                print(f"   - {col_name}: {data_type}")
            
            # Check task_corrections columns
            result = conn.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'task_corrections'
                ORDER BY ordinal_position;
            """)
            columns = result.fetchall()
            print("📋 task_corrections columns:")
            for col_name, data_type in columns:
                print(f"   - {col_name}: {data_type}")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Test the correction handler workflow")
        print("   2. Verify database operations work")
        print("   3. Test with actual email processing")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_correction_database()
    sys.exit(0 if success else 1) 