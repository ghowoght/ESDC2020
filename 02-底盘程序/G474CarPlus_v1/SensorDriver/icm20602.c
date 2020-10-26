/**

 * ICM20602.c
 * @author ChrisP @ M-HIVE

 * This library source code has been created for STM32F4. Only supports SPI.
 *
 * Development environment specifics:
 * STM32CubeIDE 1.0.0
 * STM32CubeF4 FW V1.24.1
 * STM32F4 LL Driver(SPI) and HAL Driver(RCC for HAL_Delay() function)
 *
 * Created by ChrisP(Wonyeob Park) @ M-HIVE Embedded Academy, July, 2019
 * Rev. 1.0
 *
 * https://github.com/ChrisWonyeobPark/
*/

/**
 * @brief ICM20602 structure definition.
 */

#include "ICM20602.h"
#include "stdio.h"

Struct_ICM20602 ICM20602;
int32_t gyro_x_offset, gyro_y_offset, gyro_z_offset; // To remove offset


void ICM20602_GPIO_SPI_Initialization(void)
{
	LL_SPI_InitTypeDef SPI_InitStruct = {0};
	
	LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

	LL_GPIO_ResetOutputPin(ICM20602_SPI_CS_PORT, ICM20602_SPI_CS_PIN);

	LL_SPI_Enable(ICM20602_SPI_CHANNEL);

	CHIP_DESELECT(ICM20602);
}


unsigned char SPI1_SendByte(unsigned char data)
{
	while(LL_SPI_IsActiveFlag_TXE(ICM20602_SPI_CHANNEL)==RESET);
	LL_SPI_TransmitData8(ICM20602_SPI_CHANNEL, data);
	
	while(LL_SPI_IsActiveFlag_RXNE(ICM20602_SPI_CHANNEL)==RESET);
	return LL_SPI_ReceiveData8(ICM20602_SPI_CHANNEL);
}

//////////////////////////////////////////////////////////////

uint8_t ICM20602_Readbyte(uint8_t reg_addr)
{
	uint8_t val;

	CHIP_SELECT(ICM20602);
	SPI1_SendByte(reg_addr | 0x80); //Register. MSB 1 is read instruction.
	val = SPI1_SendByte(0x00); //Send DUMMY to read data
	CHIP_DESELECT(ICM20602);
	
	return val;
}

void ICM20602_Readbytes(unsigned char reg_addr, unsigned char len, unsigned char* data)
{
	unsigned int i = 0;

	CHIP_SELECT(ICM20602);
	SPI1_SendByte(reg_addr | 0x80); //Register. MSB 1 is read instruction.
	while(i < len)
	{
		data[i++] = SPI1_SendByte(0x00); //Send DUMMY to read data
	}
	CHIP_DESELECT(ICM20602);
}

void ICM20602_Writebyte(uint8_t reg_addr, uint8_t val)
{
	CHIP_SELECT(ICM20602);
	SPI1_SendByte(reg_addr & 0x7F); //Register. MSB 0 is write instruction.
	SPI1_SendByte(val); //Send Data to write
	CHIP_DESELECT(ICM20602);
}

void ICM20602_Writebytes(unsigned char reg_addr, unsigned char len, unsigned char* data)
{
	unsigned int i = 0;
	CHIP_SELECT(ICM20602);
	SPI1_SendByte(reg_addr & 0x7F); //Register. MSB 0 is write instruction.
	while(i < len)
	{
		SPI1_SendByte(data[i++]); //Send Data to write
	}
	CHIP_DESELECT(ICM20602);
}


int ICM20602_Initialization(void)
{

	uint8_t who_am_i = 0;
	int16_t accel_raw_data[3] = {0};  // To remove offset
	int16_t gyro_raw_data[3] = {0};   // To remove offset
	
	ICM20602_GPIO_SPI_Initialization();
	
	printf("Checking ICM20602...");
	
	// check WHO_AM_I (0x75)
	who_am_i = ICM20602_Readbyte(WHO_AM_I); 
	
	// who am i = 0x12
	if(who_am_i == 0x12)
	{
		printf("\nICM20602 who_am_i = 0x%02x...OK\n\n", who_am_i);
	}
	// recheck
	else if(who_am_i != 0x12)
	{
		who_am_i = ICM20602_Readbyte(WHO_AM_I); // check again WHO_AM_I (0x75)

		if (who_am_i != 0x12){
			printf( "ICM20602 Not OK: 0x%02x Should be 0x%02x\n", who_am_i, 0x12);
			return 1; //ERROR
		}
	}
	
	// Reset ICM20602
	// PWR_MGMT_1 0x6B
	ICM20602_Writebyte(PWR_MGMT_1, 0x80); //Reset ICM20602
	HAL_Delay(50);

	// PWR_MGMT_1 0x6B
	ICM20602_Writebyte(PWR_MGMT_1, 0x01); // Enable Temperature sensor(bit4-0), Use PLL(bit2:0-01)
									// 온도센서 끄면 자이로 값 이상하게 출력됨
	HAL_Delay(50);

	// PWR_MGMT_2 0x6C
	//ICM20602_Writebyte(PWR_MGMT_2, 0x38); // Disable Acc(bit5:3-111), Enable Gyro(bit2:0-000)
	ICM20602_Writebyte( PWR_MGMT_2, 0x00 ); // Enable Acc(bit5:3-000), Enable Gyro(bit2:0-000)
	HAL_Delay(50);
	
	// set sample rate to 1000Hz and apply a software filter
	ICM20602_Writebyte(SMPLRT_DIV, 0x00);
	HAL_Delay(50);
	
	// Gyro DLPF Config
	//ICM20602_Writebyte(CONFIG, 0x00); // Gyro LPF fc 250Hz(bit2:0-000)
	ICM20602_Writebyte(CONFIG, 0x05); // Gyro LPF fc 20Hz(bit2:0-100) at 1kHz sample rate
	HAL_Delay(50);

	// GYRO_CONFIG 0x1B
	ICM20602_Writebyte(GYRO_CONFIG, 0x18); // Gyro sensitivity 2000 dps(bit4:3-11), FCHOICE (bit1:0-00)
	HAL_Delay(50);

	// ACCEL_CONFIG 0x1C
	ICM20602_Writebyte(ACCEL_CONFIG, 0x18); // Acc sensitivity 16g
	HAL_Delay(50);
	
	// ACCEL_CONFIG2 0x1D
	ICM20602_Writebyte(ACCEL_CONFIG2, 0x03); // Acc FCHOICE 1kHz(bit3-0), DLPF fc 44.8Hz(bit2:0-011)
	HAL_Delay(50);
	
	// Enable Interrupts when data is ready
	ICM20602_Writebyte(INT_ENABLE, 0x01); // Enable DRDY Interrupt
	HAL_Delay(50);
	
	printf("keep quiet\n");
	HAL_Delay(500);
	gyro_x_offset = gyro_y_offset = gyro_z_offset = 0;
	const int WIN = 500;
	for(int i = 0; i < WIN; )
  {
		if(ICM20602_DataReady())
		{
			short gyro[3] = {0};
			ICM20602_Get3AxisGyroRawData(gyro);
			gyro_x_offset += gyro[0];
			gyro_y_offset += gyro[1];
			gyro_z_offset += gyro[2];
			i++;
		}
	}
	gyro_x_offset /= WIN;
	gyro_y_offset /= WIN;
	gyro_z_offset /= WIN;
	
	gyro_x_offset = -gyro_x_offset;
	gyro_y_offset = -gyro_y_offset;
	gyro_z_offset = -gyro_z_offset;
	
	printf("gyro bias: %d %d %d\n", gyro_x_offset, gyro_y_offset, gyro_z_offset);

	// Remove Gyro X offset
	ICM20602_Writebyte( XG_OFFS_USRH, gyro_x_offset>>8 );	// gyro x offset high byte
	ICM20602_Writebyte( XG_OFFS_USRL, gyro_x_offset );	// gyro x offset low byte
	
	// Remove Gyro Y offset
	ICM20602_Writebyte( YG_OFFS_USRH, gyro_y_offset>>8 );	// gyro y offset high byte
	ICM20602_Writebyte( YG_OFFS_USRL, gyro_y_offset );	// gyro y offset low byte
	
	// Remove Gyro Z offset
	ICM20602_Writebyte( ZG_OFFS_USRH, gyro_z_offset>>8 );	// gyro z offset high byte
	ICM20602_Writebyte( ZG_OFFS_USRL, gyro_z_offset );	// gyro z offset low byte

	return 0; //OK
}
#include "Sensor_Basic.h"
void ICM20602_Get6AxisRawData(short *accel, short *gyro)
{
	unsigned char data[14];
	ICM20602_Readbytes(ACCEL_XOUT_H, 14, data);
	

	accel[0] = (data[0] << 8) | data[1];
	accel[1] = (data[2] << 8) | data[3];
	accel[2] = (data[4] << 8) | data[5];

	gyro[0] = ((data[8] << 8) | data[9]);
	gyro[1] = ((data[10] << 8) | data[11]);
	gyro[2] = ((data[12] << 8) | data[13]);
	
//	sensor.Tempreature = ((((int16_t)data[6]) << 8) | data[7]); //tempreature
//	/*icm20602温度*/
//	sensor.Tempreature_C = sensor.Tempreature/326.8f + 25 ;//sensor.Tempreature/340.0f + 36.5f;

//	//调整物理坐标轴与软件坐标轴方向定义一致
//	sensor.Acc_Original[X] = accel[X];
//	sensor.Acc_Original[Y] = accel[Y];
//	sensor.Acc_Original[Z] = accel[Z];
//	
//	sensor.Gyro_Original[X] = gyro[X];
//	sensor.Gyro_Original[Y] = gyro[Y];
//	sensor.Gyro_Original[Z] = gyro[Z];
	
}

void ICM20602_Get3AxisGyroRawData(short* gyro)
{
	unsigned char data[6];
	ICM20602_Readbytes(GYRO_XOUT_H, 6, data);
	
	gyro[0] = ((data[0] << 8) | data[1]);
	gyro[1] = ((data[2] << 8) | data[3]);
	gyro[2] = ((data[4] << 8) | data[5]);
}

void ICM20602_Get3AxisAccRawData(short* accel)
{
	unsigned char data[6];
	ICM20602_Readbytes(ACCEL_XOUT_H, 6, data);
	
	accel[0] = ((data[0] << 8) | data[1]);
	accel[1] = ((data[2] << 8) | data[3]);
	accel[2] = ((data[4] << 8) | data[5]);
}

int ICM20602_DataReady(void)
{
	return LL_GPIO_IsInputPinSet(ICM20602_INT_PORT, ICM20602_INT_PIN);
}

#include "Scheduler.h"
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
		if(GPIO_Pin == GPIO_PIN_12)
		{
			INT_1ms_Task();
		}
	
}
